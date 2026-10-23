import asyncio
from uuid import uuid4

from pydantic import ValidationError

from match_context.analysis.metrics import compute_facts
from match_context.analysis.patterns import detect_stories
from match_context.domain.contracts import ContextResult, TraceStep
from .base import AgentLimits, AgentOutput, BudgetExceeded, RunBudget
from .fallback import build_factual_result
from .tools import ToolDenied, make_scoped_tools
from .validation import check_draft, render_card, validate_claims


def prepare_tools(snapshot, request, *, budget=None):
    if request.match_id != snapshot.metadata.match_id or request.to_sequence != snapshot.cutoff:
        raise ValueError("Request and snapshot must share match and cutoff")
    candidates = detect_stories(snapshot, request)
    facts = {fact.fact_id: fact for fact in compute_facts(snapshot, request.from_sequence, snapshot.cutoff)}
    windows = {(interval.start_second, interval.end_second) for candidate in candidates
               for interval in (candidate.current_interval, candidate.comparison_interval)}
    for lower, upper in sorted(windows):
        for fact in compute_facts(snapshot, 0, snapshot.cutoff, start_second=lower, end_second=upper):
            facts[fact.fact_id] = fact
    return make_scoped_tools(snapshot, tuple(facts.values()), candidates=candidates, budget=budget)


def _parse(output):
    if isinstance(output, AgentOutput):
        return AgentOutput.model_validate(output.model_dump())
    if isinstance(output, str):
        return AgentOutput.model_validate_json(output)
    return AgentOutput.model_validate(output)


async def orchestrate(snapshot, request, runner, *, limits: AgentLimits | None = None) -> ContextResult:
    budget = RunBudget(limits=limits or AgentLimits())
    tools = prepare_tools(snapshot, request, budget=budget)
    trace_id = str(uuid4())
    rejected_codes = set()
    mode = runner.mode
    if mode not in ("foundry", "scripted"):
        raise ValueError("Unsupported agent mode")

    def fallback(code):
        rejected_codes.add(code)
        budget.steps.append(TraceStep(role="system", decision="factual_fallback"))
        return build_factual_result(snapshot, request, tools.facts, tools=tools, trace_id=trace_id,
                                    rejection_codes=tuple(rejected_codes))

    base = {"request": request.model_dump(mode="json"), "snapshot_id": snapshot.snapshot_id,
            "cutoff": snapshot.cutoff, "entities": dict(tools.entities)}

    async def invoke(role, payload):
        budget.steps.append(TraceStep(role=role, decision="started"))
        timeout = budget.remaining()
        output = await asyncio.wait_for(runner.run(role, payload, tools), timeout=timeout)
        return _parse(output)

    try:
        if not tools.candidates:
            return fallback("no_supported_change")
        analysis = await invoke("analyst", base)
        known = {candidate.story_id: candidate for candidate in tools.candidates}
        identifiers = analysis.selected_story_ids
        if (not identifiers or len(set(identifiers)) != len(identifiers) or not set(identifiers) <= known.keys()
                or analysis.cards or analysis.decisions):
            return fallback("invalid_selection")
        count = 1 if request.role == "fan" and request.depth == "simple" else 3
        pending = list(identifiers[:count])
        accepted = {}
        for attempt in range(2):
            if attempt:
                budget.steps.append(TraceStep(role="writer", decision="repair_requested"))
            payload = {**base, "stories": [tools.story_payload(known[identifier]) for identifier in pending],
                       "repair": attempt == 1, "rejection_codes": sorted(rejected_codes)}
            try:
                written = await invoke("writer", payload)
            except (ValueError, ValidationError):
                rejected_codes.add("invalid_output")
                continue
            if (written.selected_story_ids or written.decisions
                    or len({card.story_id for card in written.cards}) != len(written.cards)
                    or any(card.story_id not in pending for card in written.cards)):
                rejected_codes.add("invalid_output")
                continue
            valid = []
            supplied = {card.story_id for card in written.cards}
            if supplied != set(pending):
                rejected_codes.add("missing_card")
            for card in written.cards:
                errors = check_draft(card, tools, known[card.story_id])
                if errors:
                    rejected_codes.update(errors)
                else:
                    valid.append(card)
            if valid:
                review = await invoke("reviewer", {**payload, "cards": [card.model_dump(mode="json") for card in valid]})
                decisions = {decision.story_id: decision for decision in review.decisions}
                if (review.cards or review.selected_story_ids or len(decisions) != len(review.decisions)
                        or set(decisions) != {card.story_id for card in valid}):
                    rejected_codes.add("invalid_review")
                else:
                    for card in valid:
                        decision = decisions[card.story_id]
                        if decision.accepted and not decision.codes:
                            accepted[card.story_id] = card
                            budget.steps.append(TraceStep(role="reviewer", decision="accepted"))
                        else:
                            rejected_codes.update(decision.codes or ("review_rejected",))
                            budget.steps.append(TraceStep(role="reviewer", decision="rejected"))
            pending = [identifier for identifier in pending if identifier not in accepted]
            if not pending:
                break
        if not accepted:
            return fallback("no_accepted_story")
        cards = tuple(render_card(accepted[identifier], tools, known[identifier], request.language)
                      for identifier in identifiers if identifier in accepted)
        summary_claims = tuple(accepted[card.story_id].suggested_line for card in cards)
        references = {identifier for claim in summary_claims for identifier in claim.event_ids}
        for card in cards:
            for claim in card.claims:
                references.update(claim.event_ids)
                for fact_id in claim.fact_ids:
                    references.update(tools.fact_map[fact_id].event_ids)
        result = ContextResult(request=request, snapshot_id=snapshot.snapshot_id, status="verified", mode=mode,
                             summary=" ".join(card.suggested_line for card in cards), summary_claims=summary_claims,
                             cards=cards, facts=tools.facts,
                             evidence_ids=tuple(event.event_id for event in snapshot.known_events if event.event_id in references),
                             rejection_codes=tuple(sorted(rejected_codes)), trace_id=trace_id, trace=budget.trace())
        report = validate_claims(result, snapshot, tools.facts)
        if report.codes:
            rejected_codes.update(report.codes)
            return fallback("final_validation")
        budget.remaining()
        return result.model_copy(update={"trace": budget.trace()})
    except (TimeoutError, BudgetExceeded, ToolDenied, ValueError) as error:
        code = "deadline" if isinstance(error, TimeoutError) else (
            "budget_exceeded" if isinstance(error, BudgetExceeded) else "invalid_output")
        return fallback(code)
    except Exception:
        # Provider exceptions may contain credentials, URLs or internal request bodies.
        return fallback("provider_error")
