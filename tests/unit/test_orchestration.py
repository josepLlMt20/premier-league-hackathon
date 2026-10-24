import asyncio

import pytest

from match_context.agents.base import AgentLimits, AgentOutput, ReviewDecision
from match_context.agents.orchestrator import orchestrate
from match_context.analysis.snapshot import build_snapshot
from match_context.domain.contracts import ContextRequest
from .agent_helpers import ScriptedRunner


@pytest.fixture
def case(scenario_main):
    cutoff = max(e.sequence for e in scenario_main.events if e.available_second <= 1500)
    snapshot = build_snapshot(scenario_main.events, cutoff, scenario_main.metadata)
    return snapshot, ContextRequest(match_id=snapshot.metadata.match_id, from_sequence=0,
                                    to_sequence=cutoff, depth="detailed")


def test_pipeline_selects_writes_reviews_and_marks_scripted_mode(case):
    runner = ScriptedRunner()
    result = asyncio.run(orchestrate(*case, runner))
    assert result.status == "verified"
    assert result.mode == "scripted"
    assert 1 <= len(result.cards) <= 3
    assert [role for role, _ in runner.calls] == ["analyst", "writer", "reviewer"]
    assert result.trace.model_calls == 0
    assert result.trace.tool_calls == 1
    assert all(len(card.overlay_text) <= 140 for card in result.cards)
    assert "{{" not in result.summary


def test_invented_fact_never_reaches_published_cards(case):
    class Inventing(ScriptedRunner):
        async def run(self, role, payload, tools):
            output = await super().run(role, payload, tools)
            if role == "writer":
                cards = tuple(card.model_copy(update={"explanation": card.explanation.model_copy(
                    update={"text": "{{fact:invented}}", "fact_ids": ("invented",)})}) for card in output.cards)
                return AgentOutput(cards=cards)
            return output

    runner = Inventing()
    result = asyncio.run(orchestrate(*case, runner))
    assert result.status == "factual"
    assert result.cards == ()
    assert "invented" not in result.model_dump_json()
    assert sum(role == "writer" for role, _ in runner.calls) == 2


def test_two_review_rejections_discard_the_story_after_only_one_repair(case):
    class Rejecting(ScriptedRunner):
        async def run(self, role, payload, tools):
            output = await super().run(role, payload, tools)
            if role == "reviewer":
                return AgentOutput(decisions=tuple(ReviewDecision(story_id=c["story_id"], accepted=False,
                                                                codes=("unsupported_meaning",)) for c in payload["cards"]))
            return output

    runner = Rejecting()
    result = asyncio.run(orchestrate(*case, runner))
    assert result.cards == ()
    assert sum(role == "writer" for role, _ in runner.calls) == 2
    assert sum(role == "reviewer" for role, _ in runner.calls) == 2
    assert result.status == "factual"


def test_malformed_json_is_repaired_once_then_falls_back(case):
    class Invalid(ScriptedRunner):
        async def run(self, role, payload, tools):
            output = await super().run(role, payload, tools)
            return "{not-json" if role == "writer" else output

    runner = Invalid()
    result = asyncio.run(orchestrate(*case, runner))
    assert result.status == "factual"
    assert sum(role == "writer" for role, _ in runner.calls) == 2
    assert any(step.decision == "repair_requested" for step in result.trace.steps)


def test_timeout_returns_identified_factual_output(case):
    class Slow(ScriptedRunner):
        called = False

        async def run(self, *args):
            self.called = True
            await asyncio.sleep(1)

    runner = Slow()
    result = asyncio.run(orchestrate(*case, runner, limits=AgentLimits(deadline_seconds=0.25)))
    assert result.status == "factual"
    assert result.mode == "factual"
    assert "deadline" in result.rejection_codes
    assert runner.called


def test_tools_and_payloads_are_new_for_each_request(case):
    runner = ScriptedRunner()
    snapshot, request = case
    asyncio.run(orchestrate(snapshot, request, runner))
    first_tools = runner.tools_seen[0]
    early = build_snapshot(snapshot.known_events, 10, snapshot.metadata)
    early_request = request.model_copy(update={"to_sequence": 10})
    early_result = asyncio.run(orchestrate(early, early_request, runner))
    assert early_result.snapshot_id == early.snapshot_id
    assert all(f.cutoff_sequence == 10 for f in early_result.facts)
    assert early_result.cards == ()
    later = asyncio.run(orchestrate(snapshot, request, runner))
    assert runner.tools_seen[-1] is not first_tools
    assert later.trace_id != early_result.trace_id


def test_mismatched_request_cannot_start_a_provider_call(case):
    snapshot, request = case
    runner = ScriptedRunner()
    with pytest.raises(ValueError):
        asyncio.run(orchestrate(snapshot, request.model_copy(update={"to_sequence": snapshot.cutoff + 1}), runner))
    assert runner.calls == []


def test_simple_and_detailed_profiles_change_selection_without_changing_facts(case):
    snapshot, request = case
    simple = asyncio.run(orchestrate(snapshot, request.model_copy(update={"depth": "simple"}), ScriptedRunner()))
    detailed = asyncio.run(orchestrate(snapshot, request, ScriptedRunner()))
    assert len(simple.cards) == 1
    assert len(detailed.cards) > len(simple.cards)
    assert simple.facts == detailed.facts


def test_accepted_stories_remain_when_another_story_is_rejected_twice(case):
    class Partial(ScriptedRunner):
        rejected_id = None

        async def run(self, role, payload, tools):
            output = await super().run(role, payload, tools)
            if role == "reviewer":
                if self.rejected_id is None:
                    self.rejected_id = payload["cards"][0]["story_id"]
                return AgentOutput(decisions=tuple(ReviewDecision(
                    story_id=c["story_id"], accepted=c["story_id"] != self.rejected_id,
                    codes=("unsupported_meaning",) if c["story_id"] == self.rejected_id else ())
                    for c in payload["cards"]))
            return output

    runner = Partial()
    result = asyncio.run(orchestrate(*case, runner))
    assert result.status == "verified"
    assert runner.rejected_id not in {card.story_id for card in result.cards}
    assert result.summary == " ".join(card.suggested_line for card in result.cards)
    assert len(result.cards) >= 1


def test_provider_exception_never_exposes_private_details(case):
    class Broken(ScriptedRunner):
        async def run(self, *args):
            raise RuntimeError("private-token-and-internal-prompt")

    result = asyncio.run(orchestrate(*case, Broken()))
    assert result.status == "factual"
    assert "provider_error" in result.rejection_codes
    assert "private-token" not in result.model_dump_json()


def test_factual_fallback_is_bilingual_with_identical_facts(case):
    snapshot, request = case

    class Broken(ScriptedRunner):
        async def run(self, *args):
            raise RuntimeError()

    es = asyncio.run(orchestrate(snapshot, request, Broken()))
    en = asyncio.run(orchestrate(snapshot, request.model_copy(update={"language": "en"}), Broken()))
    assert es.facts == en.facts
    assert "Resumen factual" in es.summary
    assert "Factual summary" in en.summary


@pytest.mark.parametrize("malformed", ["{bad json", {"decisions": "invalid"}])
def test_malformed_first_review_gets_the_single_batch_repair(case, malformed):
    class InvalidReview(ScriptedRunner):
        reviewed = 0

        async def run(self, role, payload, tools):
            output = await super().run(role, payload, tools)
            if role == "reviewer":
                self.reviewed += 1
                if self.reviewed == 1:
                    return malformed
            return output

    runner = InvalidReview()
    result = asyncio.run(orchestrate(*case, runner))
    assert result.status == "verified"
    assert "invalid_review" in result.rejection_codes
    assert [role for role, _ in runner.calls] == ["analyst", "writer", "reviewer", "writer", "reviewer"]
    assert runner.calls[3][1]["repair"] is True
    assert "invalid_review" in runner.calls[3][1]["rejection_codes"]


def test_malformed_repair_review_keeps_previously_accepted_stories(case):
    class PartialReview(ScriptedRunner):
        rejected_id = None

        async def run(self, role, payload, tools):
            output = await super().run(role, payload, tools)
            if role == "reviewer":
                if self.rejected_id is not None:
                    return "{bad json"
                self.rejected_id = payload["cards"][0]["story_id"]
                return AgentOutput(decisions=tuple(ReviewDecision(
                    story_id=card["story_id"], accepted=card["story_id"] != self.rejected_id,
                    codes=("unsupported_meaning",) if card["story_id"] == self.rejected_id else ())
                    for card in payload["cards"]))
            return output

    runner = PartialReview()
    result = asyncio.run(orchestrate(*case, runner))
    assert result.status == "verified"
    assert result.cards and all(card.story_id != runner.rejected_id for card in result.cards)
    assert "invalid_review" in result.rejection_codes
    assert sum(role == "writer" for role, _ in runner.calls) == 2
    assert sum(role == "reviewer" for role, _ in runner.calls) == 2
