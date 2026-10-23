from uuid import uuid4

from match_context.domain.contracts import Claim, ContextResult
from .tools import make_scoped_tools
from .validation import render_claim


def build_factual_result(snapshot, request, facts, *, tools=None, trace_id=None, rejection_codes=()):
    tools = tools or make_scoped_tools(snapshot, facts)
    selected = [fact for fact in facts if fact.name == "shots"
                and fact.interval.start_sequence == request.from_sequence
                and fact.interval.end_sequence == request.to_sequence and fact.interval.start_second is None]
    claims = tuple(Claim(claim_id=f"fallback-{index}", kind="observed",
                         text="{{entity:" + fact.team_id + "}}: {{fact:" + fact.fact_id + "}} "
                              + ("tiros en el tramo." if request.language == "es" else "shots in this interval."),
                         fact_ids=(fact.fact_id,)) for index, fact in enumerate(selected))
    observations = sum(request.from_sequence < e.sequence <= request.to_sequence for e in snapshot.known_events)
    label = "Resumen factual. " if request.language == "es" else "Factual summary. "
    if observations < 10:
        label += "Observaciones limitadas. " if request.language == "es" else "Limited observations. "
    return ContextResult(request=request, snapshot_id=snapshot.snapshot_id,
                         status="insufficient" if observations < 10 else "factual", mode="factual",
                         summary=label + " ".join(render_claim(claim, tools) for claim in claims),
                         summary_claims=claims, facts=facts,
                         evidence_ids=tuple(dict.fromkeys(identifier for fact in selected for identifier in fact.event_ids)),
                         rejection_codes=tuple(sorted(set(rejection_codes))), trace_id=trace_id or str(uuid4()),
                         trace=tools.budget.trace())
