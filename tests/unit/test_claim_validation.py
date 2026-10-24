import pytest

from match_context.agents.orchestrator import prepare_tools
from match_context.agents.tools import ToolDenied, make_scoped_tools
from match_context.agents.validation import check_claim, render_claim, validate_claims
from match_context.agents.orchestrator import orchestrate
from .agent_helpers import ScriptedRunner
import asyncio
from match_context.analysis.snapshot import build_snapshot
from match_context.domain.contracts import Claim, ContextRequest
from match_context.agents.base import AgentLimits, BudgetExceeded, RunBudget


@pytest.fixture
def scoped(scenario_main):
    cutoff = max(e.sequence for e in scenario_main.events if e.available_second <= 1500)
    snapshot = build_snapshot(scenario_main.events, cutoff, scenario_main.metadata)
    request = ContextRequest(match_id=snapshot.metadata.match_id, from_sequence=0, to_sequence=cutoff)
    return prepare_tools(snapshot, request)


def test_tools_reject_unknown_or_future_references(scoped):
    with pytest.raises(ToolDenied):
        scoped.inspect_events(["future-event"], scoped.snapshot.cutoff)
    with pytest.raises(ToolDenied):
        scoped.list_candidates(scoped.snapshot.cutoff + 1)
    with pytest.raises(ToolDenied):
        scoped.read_facts(["invented"], scoped.snapshot.cutoff)


def test_tools_reject_forged_metrics_even_with_a_valid_fact_identifier(scoped):
    fact = scoped.facts[0].model_copy(update={"value": 999})
    with pytest.raises(ValueError):
        make_scoped_tools(scoped.snapshot, (fact,))


def test_tool_budget_is_shared_across_different_tools(scoped):
    limited = make_scoped_tools(scoped.snapshot, scoped.facts, candidates=scoped.candidates,
                                budget=RunBudget(limits=AgentLimits(tool_calls=1)))
    limited.list_candidates(scoped.snapshot.cutoff)
    with pytest.raises(BudgetExceeded):
        limited.read_facts([scoped.facts[0].fact_id], scoped.snapshot.cutoff)
    assert limited.budget.trace().tool_calls == 1


def test_numeric_and_entity_markers_render_from_trusted_registry(scoped):
    fact = next(f for f in scoped.facts if f.name == "high_recoveries" and f.team_id == "amber"
                and f.interval.start_second == 1200 and f.interval.end_second == 1500)
    claim = Claim(claim_id="c1", kind="observed",
                  text="{{entity:amber}}: {{fact:" + fact.fact_id + "}} recuperaciones altas.",
                  fact_ids=(fact.fact_id,), event_ids=())
    assert check_claim(claim, scoped) == ()
    assert render_claim(claim, scoped) == "Ámbar FC: 4 recuperaciones altas."


@pytest.mark.parametrize("text", ["Tiene 999 goles.", "Tiene ９ goles.", "{{fact:invented}} goles.",
                                  "{{entity:outsider}} domina.", "{{bad:token}}", "Cobalto United domina.",
                                  "｛｛entity:outsider｝｝ domina."])
def test_free_numbers_unknown_markers_and_raw_match_names_are_rejected(scoped, text):
    claim = Claim(claim_id="c1", kind="observed", text=text,
                  fact_ids=(scoped.facts[0].fact_id,), event_ids=())
    assert check_claim(claim, scoped)


def test_strong_causality_and_unsupported_interpretation_are_rejected(scoped):
    claim = Claim(claim_id="c1", kind="interpretation", text="El cambio causó el dominio.",
                  fact_ids=(scoped.facts[0].fact_id,), event_ids=(), limitations=("Hipótesis.",))
    assert "causal_language" in check_claim(claim, scoped)
    unsupported = Claim(claim_id="c2", kind="interpretation", text="Parece un cambio de ritmo.")
    assert "missing_support" in check_claim(unsupported, scoped)


def test_public_text_cannot_diverge_from_its_validated_claims(scoped):
    request = ContextRequest(match_id=scoped.snapshot.metadata.match_id, from_sequence=0,
                             to_sequence=scoped.snapshot.cutoff)
    result = asyncio.run(orchestrate(scoped.snapshot, request, ScriptedRunner()))
    card = result.cards[0].model_copy(update={"overlay_text": "999 goals for outsiders"})
    tampered = result.model_copy(update={"cards": (card,), "summary": "Leaked future goal"})
    assert validate_claims(tampered, scoped.snapshot, scoped.facts).codes


def test_interpretation_limitations_survive_public_rendering(scoped):
    from match_context.agents.validation import render_card
    from .agent_helpers import draft_for
    story = scoped.candidates[0]
    draft = draft_for(scoped.story_payload(story))
    explanation = draft.explanation.model_copy(update={"kind": "interpretation",
                                                      "limitations": ("No hay seguimiento continuo de posiciones.",)})
    card = render_card(draft.model_copy(update={"explanation": explanation}), scoped, story, "es")
    assert "No hay seguimiento continuo de posiciones." in card.limitations


@pytest.mark.parametrize("number", ["௲", "Ⅹ", "①", "½"])
@pytest.mark.parametrize("in_limitation", [False, True])
def test_numeric_symbols_are_rejected_in_text_and_limitations(scoped, number, in_limitation):
    claim = Claim(claim_id="numeric", kind="observed",
                  text="Observación acotada." if in_limitation else f"Han marcado {number} goles.",
                  fact_ids=(scoped.facts[0].fact_id,),
                  limitations=(f"Solo {number} observaciones.",) if in_limitation else ())
    assert "free_number" in check_claim(claim, scoped)


@pytest.mark.parametrize("wording", ["recovery count rose from {before} to {now}",
                                   "Recoveries up {now} (was {before})",
                                   "Recuperaciones: {before} a {now}"])
def test_high_recovery_counts_cannot_be_published_as_total_recoveries(scoped, wording):
    facts = {fact.interval.start_second: fact for fact in scoped.facts
             if fact.name == "high_recoveries" and fact.team_id == "amber"
             and fact.interval.start_second in (900, 1200) and fact.interval.end_second in (1200, 1500)}
    before, now = facts[900], facts[1200]
    assert (before.value, now.value) == (1, 4)
    total = {fact.interval.start_second: fact for fact in scoped.facts
             if fact.name == "recoveries" and fact.team_id == "amber"
             and fact.interval.start_second in (900, 1200) and fact.interval.end_second in (1200, 1500)}
    assert (total[900].value, total[1200].value) == (5, 5)
    claim = Claim(claim_id="ambiguous-recovery", kind="observed",
                  text=wording.format(before="{{fact:" + before.fact_id + "}}",
                                      now="{{fact:" + now.fact_id + "}}"),
                  fact_ids=(before.fact_id, now.fact_id))
    assert "missing_metric_qualifier" in check_claim(claim, scoped)


@pytest.mark.parametrize("label", ["High recoveries", "Recuperaciones altas"])
def test_high_recovery_claims_keep_their_explicit_metric_qualifier(scoped, label):
    fact = next(f for f in scoped.facts if f.name == "high_recoveries" and f.team_id == "amber")
    claim = Claim(claim_id="qualified-recovery", kind="observed",
                  text=label + ": {{fact:" + fact.fact_id + "}}.", fact_ids=(fact.fact_id,))
    assert check_claim(claim, scoped) == ()
