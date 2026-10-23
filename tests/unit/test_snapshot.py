import pytest
from pydantic import ValidationError

from match_context.analysis.snapshot import build_snapshot
from match_context.analysis.evidence import resolve_evidence


def scores(snapshot):
    return {score.team_id: score.goals for score in snapshot.score}


def test_late_correction_does_not_change_an_earlier_view(metadata, make_event):
    events = [make_event(sequence=i) for i in range(1, 31)]
    events[8] = make_event(sequence=9, kind="shot")
    events[9] = make_event(sequence=10, kind="goal", attributes={"shot_event_id": "e9"})
    events[29] = make_event(sequence=30, kind="correction", attributes={"target_event_id": "e10", "action": "annul"})
    before = build_snapshot(tuple(events), 20, metadata)
    after = build_snapshot(tuple(events), 30, metadata)
    assert scores(before) == {"a": 1, "b": 0}
    assert scores(after) == {"a": 0, "b": 0}
    assert scores(before) == {"a": 1, "b": 0}
    assert "e30" not in before.model_dump_json()
    assert "e10" in {event.event_id for event in after.known_events}
    assert "e10" not in {event.event_id for event in after.effective_events}


def test_future_data_does_not_affect_hash_or_public_snapshot(metadata, make_event):
    prefix = tuple(make_event(sequence=i) for i in range(1, 4))
    future = make_event(sequence=4, kind="shot").model_copy(update={"match_id": "unrelated"})
    first = build_snapshot(prefix, 3, metadata)
    with_future = build_snapshot(prefix + (future,), 3, metadata)
    assert with_future == first
    assert "e4" not in with_future.model_dump_json()


def test_annulled_shot_also_removes_linked_goal(metadata, make_event):
    events = (make_event(kind="shot"), make_event(sequence=2, kind="goal"),
              make_event(sequence=3, kind="correction"))
    after = build_snapshot(events, 3, metadata)
    assert scores(after) == {"a": 0, "b": 0}
    assert set(after.annulled_event_ids) == {"e1", "e2"}


def test_same_payload_duplicate_does_not_duplicate_state(metadata, make_event):
    event = make_event(kind="shot")
    assert build_snapshot((event, event), 1, metadata) == build_snapshot((event,), 1, metadata)
    conflict = event.model_copy(update={"player_id": "a2"})
    with pytest.raises(ValueError, match="conflict"):
        build_snapshot((event, conflict), 1, metadata)


@pytest.mark.parametrize("cutoff", [-1, 2, True, 0.5])
def test_invalid_or_unavailable_cutoff_is_rejected(metadata, make_event, cutoff):
    with pytest.raises(ValueError):
        build_snapshot((make_event(),), cutoff, metadata)


def test_empty_snapshot_is_valid_and_has_no_invented_events(metadata):
    snapshot = build_snapshot((), 0, metadata)
    assert scores(snapshot) == {"a": 0, "b": 0}
    assert snapshot.cutoff_second == 0
    assert snapshot.known_events == snapshot.effective_events == ()


def test_snapshot_and_its_nested_values_are_immutable(metadata, make_event):
    snapshot = build_snapshot((make_event(),), 1, metadata)
    with pytest.raises(ValidationError):
        snapshot.known_events[0].attributes.completed = False
    with pytest.raises(ValidationError):
        snapshot.metadata.teams[0].name = "Changed"


def test_evidence_denies_future_and_foreign_ids(metadata, make_event):
    events = (make_event(), make_event(sequence=2))
    snapshot = build_snapshot(events, 1, metadata)
    assert resolve_evidence(snapshot, ("e1",)).events == (events[0],)
    for identifier in ("e2", "other-match-event"):
        with pytest.raises(ValueError, match="Evidence"):
            resolve_evidence(snapshot, (identifier,))


def test_evidence_marks_annulled_events_and_includes_the_correction(metadata, make_event):
    snapshot = build_snapshot((make_event(), make_event(sequence=2, kind="correction")), 2, metadata)
    evidence = resolve_evidence(snapshot, ("e1",))
    assert {e.event_id for e in evidence.events} == {"e1", "e2"}
    assert evidence.annulled_event_ids == ("e1",)


def test_invalid_known_events_are_not_silently_filtered(metadata, make_event):
    with pytest.raises(ValueError):
        build_snapshot((make_event(match_id="foreign"),), 1, metadata)


@pytest.mark.parametrize("late_player", ["actor", "recipient"])
def test_late_pass_uses_the_lineup_at_occurrence_time(scenario_main, make_event, late_player):
    metadata = scenario_main.metadata
    substitution = make_event(match_id=metadata.match_id, kind="substitution", team_id="amber", player_id="amber-01",
        occurred_second=100, available_second=100,
        attributes={"replaced_player_id": "amber-01", "replacement_player_id": "amber-12"})
    event = make_event(sequence=2, match_id=metadata.match_id, team_id="amber",
        player_id="amber-01" if late_player == "actor" else "amber-02",
        occurred_second=90, available_second=110,
        attributes={"recipient_id": "amber-02" if late_player == "actor" else "amber-01", "completed": True})
    snapshot = build_snapshot((substitution, event), 2, metadata)
    assert snapshot.known_events[1] == event


@pytest.mark.parametrize("player,occurred,valid", [
    ("amber-01", 110, False), ("amber-12", 90, False), ("amber-12", 100, True),
])
def test_historical_lineup_validation_still_rejects_inactive_players(scenario_main, make_event, player, occurred, valid):
    metadata = scenario_main.metadata
    substitution = make_event(match_id=metadata.match_id, kind="substitution", team_id="amber", player_id="amber-01",
        occurred_second=100, available_second=100,
        attributes={"replaced_player_id": "amber-01", "replacement_player_id": "amber-12"})
    event = make_event(sequence=2, match_id=metadata.match_id, team_id="amber", player_id=player,
        occurred_second=occurred, available_second=110,
        attributes={"recipient_id": "amber-02", "completed": True})
    if valid:
        assert build_snapshot((substitution, event), 2, metadata).cutoff == 2
    else:
        with pytest.raises(ValueError, match="active"):
            build_snapshot((substitution, event), 2, metadata)


def test_unsupported_substitution_annulment_is_rejected_explicitly(scenario_main, make_event):
    metadata = scenario_main.metadata
    substitution = make_event(match_id=metadata.match_id, kind="substitution", team_id="amber", player_id="amber-01",
        occurred_second=100, available_second=100,
        attributes={"replaced_player_id": "amber-01", "replacement_player_id": "amber-12"})
    correction = make_event(sequence=2, match_id=metadata.match_id, kind="correction", team_id="amber", player_id=None,
        occurred_second=110, available_second=110, attributes={"target_event_id": "e1", "action": "annul"})
    with pytest.raises(ValueError, match="[Ss]ubstitution"):
        build_snapshot((substitution, correction), 2, metadata)


def test_goal_cannot_occur_before_its_linked_shot(metadata, make_event):
    shot = make_event(kind="shot", occurred_second=100, available_second=100)
    goal = make_event(sequence=2, kind="goal", occurred_second=90, available_second=110)
    with pytest.raises(ValueError, match="shot"):
        build_snapshot((shot, goal), 2, metadata)
