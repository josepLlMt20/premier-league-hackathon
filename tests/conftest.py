import pytest

from match_context.domain.events import MatchEvent, MatchMetadata


@pytest.fixture
def metadata():
    return MatchMetadata.model_validate({
        "match_id": "match-1",
        "teams": [
            {"team_id": team, "name": name, "players": [
                {"player_id": f"{team}{i}", "name": f"{name} {i}"}
                for i in range(1, 4)
            ]}
            for team, name in (("a", "Amber"), ("b", "Cobalt"))
        ],
        "attack_directions": [
            {"team_id": team, "period": period, "direction": direction}
            for team, period, direction in (("a", 1, 1), ("a", 2, -1), ("b", 1, -1), ("b", 2, 1))
        ],
    })


@pytest.fixture
def make_event():
    def make(**overrides):
        sequence = overrides.get("sequence", 1)
        kind = overrides.get("kind", "pass")
        details = {
            "pass": {"recipient_id": "a2", "completed": True, "under_pressure": False},
            "shot": {"on_target": True, "under_pressure": False},
            "goal": {"shot_event_id": "e1"},
            "correction": {"target_event_id": "e1", "action": "annul"},
            "substitution": {"replaced_player_id": "a1", "replacement_player_id": "a3"},
            "turnover": {"to_team_id": "b"},
        }.get(kind, {})
        data = {
            "match_id": "match-1", "event_id": f"e{sequence}", "sequence": sequence,
            "occurred_second": sequence * 10, "available_second": sequence * 10,
            "period": 1, "kind": kind, "team_id": "a", "player_id": "a1",
            "start": {"x": 20, "y": 34}, "end": {"x": 30, "y": 34},
            "attributes": details,
        }
        data.update(overrides)
        return MatchEvent.model_validate(data)
    return make


@pytest.fixture
def scenario_main():
    from match_context.simulation.generator import generate_match
    return generate_match("main", 7)


@pytest.fixture
def scenario_neutral():
    from match_context.simulation.generator import generate_match
    return generate_match("neutral", 11)


@pytest.fixture
def scenario_sterile():
    from match_context.simulation.generator import generate_match
    return generate_match("sterile", 19)


@pytest.fixture
def scenario_correction():
    from match_context.simulation.generator import generate_match
    return generate_match("correction", 23)
