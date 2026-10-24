"""Publication regressions for useful, correctly labeled editorial copy."""
import asyncio
import pytest
from match_context.agents.base import AgentOutput
from match_context.agents.orchestrator import orchestrate, prepare_tools
from match_context.agents.validation import check_claim, check_draft, validate_claims
from match_context.analysis.snapshot import build_snapshot
from match_context.domain.contracts import Claim, ContextRequest
from tests.e2e_server import BilingualScriptedRunner
from .agent_helpers import draft_for, ScriptedRunner

@pytest.fixture
def editorial_case(scenario_main):
    cutoff = max(e.sequence for e in scenario_main.events if e.available_second <= 1728)
    snapshot = build_snapshot(scenario_main.events, cutoff, scenario_main.metadata)
    request = ContextRequest(match_id=snapshot.metadata.match_id, from_sequence=0,
                             to_sequence=cutoff, role="commentator", depth="detailed")
    return snapshot, request, prepare_tools(snapshot, request)

@pytest.mark.parametrize("language", ["es", "en"])
def test_scripted_commentator_names_metrics_and_gives_each_field_a_job(editorial_case, language):
    snapshot, request, tools = editorial_case
    result = asyncio.run(orchestrate(snapshot, request.model_copy(update={"language": language}), BilingualScriptedRunner()))
    assert result.status == "verified" and result.mode == "scripted"
    assert len(result.cards) == 3
    assert not validate_claims(result, snapshot, result.facts).codes
    for card in result.cards:
        assert len({card.headline, card.explanation, card.suggested_line}) == 3
        assert len(card.overlay_text) <= 140
        candidate = next(c for c in tools.candidates if c.story_id == card.story_id)
        if candidate.pattern == "chance_quality":
            label = "tiros" if language == "es" else "shots"
            assert label in card.explanation.lower() and label in card.suggested_line.lower()
            assert "148" not in card.headline and "148" not in card.suggested_line
            assert ("puntos" if language == "es" else "points") in card.explanation
            assert ("sintético" if language == "es" else "synthetic") in card.explanation
        elif candidate.pattern == "territorial_shift":
            assert "%" in card.explanation and "%" in card.overlay_text
            assert ("ambos equipos" if language == "es" else "both teams") in card.explanation
            assert ("último tercio" if language == "es" else "attacking-third") in card.explanation

@pytest.mark.parametrize("metric, wording", [
    ("shot_quality_total", "{{entity:amber}}: {value}, antes nada."),
    ("shot_quality_total", "Índice sintético de tiro: {value}."),
    ("territorial_share", "{{entity:amber}}: {value}, antes nada."),
    ("territorial_share", "Cuota de pases en el último tercio: {value}."),
])
def test_bare_editorial_metric_values_or_missing_units_are_rejected(editorial_case, metric, wording):
    _, _, tools = editorial_case
    fact = next(f for f in tools.facts if f.name == metric and f.team_id == "amber")
    text = wording.replace("{value}", "{{fact:" + fact.fact_id + "}}")
    claim = Claim(claim_id="bare", kind="observed", text=text, fact_ids=(fact.fact_id,))
    assert "missing_metric_qualifier" in check_claim(claim, tools)

@pytest.mark.parametrize("metric, label", [
    ("shot_quality_total", "Índice sintético de tiro: {value} puntos."),
    ("shot_quality_total", "Synthetic shot-quality index: {value} points."),
    ("territorial_share", "Cuota de pases completados en el último tercio: {value}%."),
    ("territorial_share", "Completed attacking-third pass share: {value}%."),
])
def test_named_metrics_with_units_remain_publishable(editorial_case, metric, label):
    _, _, tools = editorial_case
    fact = next(f for f in tools.facts if f.name == metric and f.team_id == "amber")
    claim = Claim(claim_id="clear", kind="observed", text=label.replace("{value}", "{{fact:" + fact.fact_id + "}}"), fact_ids=(fact.fact_id,))
    assert check_claim(claim, tools) == ()


def test_exact_repeated_main_fields_are_rejected_even_with_different_claim_ids(editorial_case):
    _, _, tools = editorial_case
    candidate = tools.candidates[0]
    draft = draft_for(tools.story_payload(candidate))
    repeated = draft.model_copy(update={"explanation": draft.headline.model_copy(update={"claim_id": "other-id", "text": draft.headline.text + "  "})})
    assert "repetitive_copy" in check_draft(repeated, tools, candidate)


def test_repeated_main_fields_are_repaired_then_fall_back_instead_of_being_published(editorial_case):
    snapshot, request, _ = editorial_case
    class Repeating(ScriptedRunner):
        async def run(self, role, payload, tools):
            result = await super().run(role, payload, tools)
            if role == "writer":
                return AgentOutput(cards=tuple(card.model_copy(update={"explanation": card.headline.model_copy(update={"claim_id": card.explanation.claim_id})}) for card in result.cards))
            return result
    result = asyncio.run(orchestrate(snapshot, request, Repeating()))
    assert result.status == "factual" and result.cards == ()
    assert "repetitive_copy" in result.rejection_codes

@pytest.mark.parametrize("shots_now", [1, 2])
def test_higher_quality_index_does_not_invent_an_increase_in_shot_volume(editorial_case, shots_now):
    _, _, tools = editorial_case
    candidate = next(c for c in tools.candidates if c.pattern == "chance_quality")
    payload = tools.story_payload(candidate)
    shot_facts = [f for f in payload["facts"] if f["name"] == "shots"]
    shot_facts[0]["value"], shot_facts[1]["value"] = 2, shots_now
    # Template input regression only; modified values are not passed as canonical
    # facts to orchestration or publication.
    draft = draft_for(payload)
    assert "volumen" not in draft.headline.text
    assert "índice sintético" in draft.suggested_line.text
