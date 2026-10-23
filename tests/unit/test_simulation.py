import pytest
from pydantic import ValidationError

from match_context.domain.events import GeneratedMatch, validate_event
from match_context.simulation.generator import generate_match
from match_context.simulation.fixtures import scenario_manifest


def test_seed_reproduces_events_and_other_seed_changes_them():
    first = generate_match("main", 7)
    assert first.model_dump_json() == generate_match("main", 7).model_dump_json()
    assert first.model_dump_json() != generate_match("main", 8).model_dump_json()


@pytest.mark.parametrize("scenario,seed", [("main", 7), ("neutral", 11), ("sterile", 19), ("correction", 23)])
def test_generated_match_is_ninety_minutes_with_valid_players_and_coordinates(scenario, seed):
    match = generate_match(scenario, seed)
    assert match.events[-1].available_second == 5400
    assert [e.sequence for e in match.events] == list(range(1, len(match.events) + 1))
    assert len({e.event_id for e in match.events}) == len(match.events)
    assert sorted(e.available_second for e in match.events) == [e.available_second for e in match.events]
    teams = {team.team_id: team for team in match.metadata.teams}
    assert {team.name for team in teams.values()} == {"Ámbar FC", "Cobalto United"}
    assert len(match.events) >= 800
    for e in match.events:
        validate_event(e)
        assert e.match_id == match.metadata.match_id
        assert e.available_second >= e.occurred_second
        assert e.period == (1 if e.occurred_second < 2700 else 2)
        if e.player_id is not None:
            assert e.player_id in {p.player_id for p in teams[e.team_id].players}
        for point in (e.start, e.end):
            if point:
                assert 0 <= point.x <= 105 and 0 <= point.y <= 68
    for lower in range(0, 5400, 300):
        assert sum(lower < e.occurred_second <= lower + 300 for e in match.events) >= 10


def test_passes_stay_with_possession_until_turnover_or_recovery(scenario_main):
    owner = None
    for e in scenario_main.events:
        if e.kind == "recovery":
            owner = e.team_id
        elif e.kind == "turnover":
            assert owner == e.team_id
            owner = e.attributes.to_team_id
        elif e.kind in ("pass", "shot", "goal"):
            assert owner == e.team_id
        if e.kind == "pass" and not e.attributes.completed:
            owner = next(t.team_id for t in scenario_main.metadata.teams if t.team_id != e.team_id)


def test_goals_reference_earlier_on_target_shots_of_same_team(scenario_main):
    shots = {e.event_id: e for e in scenario_main.events if e.kind == "shot"}
    goals = [e for e in scenario_main.events if e.kind == "goal"]
    assert goals
    assert any(e.kind == "pass" and not e.attributes.completed for e in scenario_main.events)
    assert any(e.kind == "substitution" for e in scenario_main.events)
    for goal in goals:
        shot = shots[goal.attributes.shot_event_id]
        assert shot.sequence < goal.sequence
        assert shot.team_id == goal.team_id
        assert shot.attributes.on_target


def test_main_has_four_high_recoveries_after_one(scenario_main):
    def count(lower, upper):
        return sum(e.kind == "recovery" and e.team_id == "amber" and e.start.x >= 70
                   for e in scenario_main.events if lower < e.occurred_second <= upper)
    assert count(900, 1200) == 1
    assert count(1200, 1500) == 4


def test_truth_manifest_is_not_in_match_payload(scenario_main):
    manifest = scenario_manifest("main")
    assert manifest.expected_patterns == ("high_recoveries", "chance_quality")
    assert "expected_patterns" not in scenario_main.model_dump_json()
    assert "scenario" not in scenario_main.metadata.model_dump()


@pytest.mark.parametrize("overrides", [
    {"sequence": 0}, {"start": {"x": 106, "y": 0}},
    {"start": {"x": float("nan"), "y": 0}},
    {"occurred_second": 20, "available_second": 10},
    {"occurred_second": 3000, "available_second": 3000, "period": 1},
    {"attributes": {"recipient_id": "a2", "completed": True, "unknown": 3}},
    {"start": None}, {"unexpected": True},
])
def test_invalid_event_is_rejected(make_event, overrides):
    with pytest.raises(ValidationError):
        make_event(**overrides)


@pytest.mark.parametrize("change", ["other_match", "future_reference", "missing_player", "duplicate", "gap"])
def test_stream_rejects_invalid_relationships(metadata, make_event, change):
    first = make_event()
    second = make_event(sequence=2, kind="correction")
    if change == "other_match":
        second = make_event(sequence=2, kind="correction", match_id="other")
    elif change == "future_reference":
        second = make_event(sequence=2, kind="correction", attributes={"target_event_id": "e3", "action": "annul"})
    elif change == "missing_player":
        second = make_event(sequence=2, player_id="unknown")
    elif change == "duplicate":
        second = first
    else:
        second = make_event(sequence=3)
    with pytest.raises(ValueError):
        GeneratedMatch(metadata=metadata, events=(first, second))


def test_unknown_scenario_is_rejected():
    with pytest.raises(ValueError, match="scenario"):
        generate_match("real-premier-league", 1)


def test_neutral_shots_include_on_and_off_target_attempts(scenario_neutral):
    assert {event.attributes.on_target for event in scenario_neutral.events if event.kind == "shot"} == {True, False}
