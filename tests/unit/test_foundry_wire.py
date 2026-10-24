import json

import pytest
from pydantic import ValidationError

from match_context.agents.base import AgentOutput
from match_context.agents.orchestrator import prepare_tools
from match_context.analysis.snapshot import build_snapshot
from match_context.domain.contracts import ContextRequest
from .agent_helpers import compact_card, draft_for


@pytest.fixture
def wire_case(scenario_main):
    from match_context.agents.wire import WireCodec
    snapshot = build_snapshot(scenario_main.events, 269, scenario_main.metadata)
    request = ContextRequest(match_id=snapshot.metadata.match_id, from_sequence=0, to_sequence=269)
    tools = prepare_tools(snapshot, request)
    return WireCodec(tools), tools


def test_each_role_requests_only_its_own_schema():
    from match_context.agents.wire import ROLE_OUTPUTS
    for role, required in (("analyst", "selected_story_ids"), ("writer", "cards"), ("reviewer", "decisions")):
        schema = ROLE_OUTPUTS[role].model_json_schema()
        assert set(schema["properties"]) == {required}
        assert len(json.dumps(schema)) < len(json.dumps(AgentOutput.model_json_schema()))
    with pytest.raises(ValidationError):
        ROLE_OUTPUTS["analyst"].model_validate({"selected_story_ids": ["a", "b", "c", "d"]})


def test_compact_writing_roundtrip_retains_support_and_interpretation_limits(wire_case):
    from match_context.agents.wire import ROLE_OUTPUTS
    codec, tools = wire_case
    draft = draft_for(tools.story_payload(tools.candidates[0]))
    draft = draft.model_copy(update={"explanation": draft.explanation.model_copy(update={
        "kind": "interpretation", "limitations": ("Observed association in synthetic data.",)})})
    card = compact_card(draft, codec)
    compact = ROLE_OUTPUTS["writer"].model_validate({"cards": [card]})
    decoded = codec.decode(compact).cards[0]
    for original, restored in zip(draft.claims(), decoded.claims()):
        assert (original.text, original.kind, original.fact_ids, original.limitations) == (
            restored.text, restored.kind, restored.fact_ids, restored.limitations)
    assert len({claim.claim_id for claim in decoded.claims()}) == 4
    assert all(not claim.event_ids for claim in decoded.claims())
    assert len(json.dumps({"cards": [card]})) < len(json.dumps({"cards": [draft.model_dump(mode="json")]})) * .65


def test_wire_support_uses_integer_indexes_and_finite_caveats(wire_case):
    from match_context.agents.wire import WireClaim
    schema = WireClaim.model_json_schema()
    assert schema["properties"]["facts"]["items"]["type"] == "integer"
    with pytest.raises(ValidationError):
        WireClaim(text="Comparison", facts=(0,), kind="observed", limits=("invented caveat",))


@pytest.mark.parametrize("language, expected", [
    ("es", "Asociación observada en datos sintéticos."),
    ("en", "Observed association in synthetic data."),
])
def test_caveats_are_localized_without_rejected_causal_phrases(wire_case, language, expected):
    from match_context.agents.wire import ROLE_OUTPUTS, WireCodec
    from match_context.agents.validation import check_draft
    _, tools = wire_case
    codec = WireCodec(tools, language=language)
    candidate = tools.candidates[0]
    card = compact_card(draft_for(tools.story_payload(candidate)), codec)
    card["explanation"]["kind"] = "interpretation"
    card["explanation"]["limits"] = ["observed_association"]
    restored = codec.decode(ROLE_OUTPUTS["writer"].model_validate({"cards": [card]})).cards[0]
    assert restored.explanation.limitations == (expected,)
    assert check_draft(restored, tools, candidate) == ()


@pytest.mark.parametrize("field", ["facts", "text", "limits"])
def test_compact_writing_rejects_unknown_aliases(wire_case, field):
    from match_context.agents.wire import ROLE_OUTPUTS
    codec, tools = wire_case
    card = compact_card(draft_for(tools.story_payload(tools.candidates[0])), codec)
    card["headline"][field] = ["f9999"] if field == "facts" else (
        ["Unknown {{fact:f9999}}"] if field == "limits" else "Unknown {{fact:f9999}}")
    with pytest.raises(ValueError):
        codec.decode(ROLE_OUTPUTS["writer"].model_validate({"cards": [card]}))


def test_aliases_are_resolved_only_within_current_snapshot(wire_case, scenario_main):
    from match_context.agents.wire import WireCodec
    codec, tools = wire_case
    early = build_snapshot(scenario_main.events, 100, scenario_main.metadata)
    request = ContextRequest(match_id=early.metadata.match_id, from_sequence=0, to_sequence=100)
    other = WireCodec(prepare_tools(early, request))
    fact_id = tools.facts[0].fact_id
    alias = codec.encode(fact_id)
    assert codec.fact_id(alias) == fact_id
    assert other.fact_id(alias) != fact_id
    with pytest.raises(ValueError):
        other.fact_id(fact_id)
