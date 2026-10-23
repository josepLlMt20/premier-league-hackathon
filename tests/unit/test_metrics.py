import pytest

from match_context.analysis.metrics import compute_facts
from match_context.analysis.snapshot import build_snapshot


def get(facts, team, name):
    return next(fact for fact in facts if fact.team_id == team and fact.name == name)


def test_metrics_use_hand_calculated_values_and_goal_is_not_a_second_shot(metadata, make_event):
    events = (
        make_event(start={"x": 10, "y": 10}, end={"x": 13, "y": 14}),
        make_event(sequence=2, start={"x": 70, "y": 34}, end={"x": 80, "y": 34},
                   attributes={"recipient_id": "a2", "completed": False}),
        make_event(sequence=3, kind="shot", start={"x": 95, "y": 34}),
        make_event(sequence=4, kind="shot", team_id="b", player_id="b1", start={"x": 10, "y": 34},
                   attributes={"on_target": True, "under_pressure": True}),
        make_event(sequence=5, kind="recovery", start={"x": 80, "y": 34}),
        make_event(sequence=6, kind="goal", attributes={"shot_event_id": "e3"}),
    )
    facts = compute_facts(build_snapshot(events, 6, metadata), 0, 6)
    expected = {"pass_attempts": 2, "completed_passes": 1, "pass_accuracy": 50,
                "pass_distance_total": 15, "shots": 1, "goals": 1,
                "high_recoveries": 1, "shot_quality_total": 80}
    for name, value in expected.items():
        assert get(facts, "a", name).value == value
    assert get(facts, "b", "shot_quality_total").value == 56
    assert get(facts, "a", "pass_accuracy").denominator == 2


def test_territorial_share_counts_only_completed_passes_at_either_end(metadata, make_event):
    events = (
        make_event(end={"x": 80, "y": 34}),
        make_event(sequence=2, end={"x": 75, "y": 34}),
        make_event(sequence=3, team_id="b", player_id="b1", end={"x": 20, "y": 34},
                   attributes={"recipient_id": "b2", "completed": True}),
        make_event(sequence=4, end={"x": 90, "y": 34},
                   attributes={"recipient_id": "a2", "completed": False}),
    )
    facts = compute_facts(build_snapshot(events, 4, metadata), 0, 4)
    assert get(facts, "a", "territorial_share").value == 66.67
    assert get(facts, "b", "territorial_share").value == 33.33
    assert get(facts, "a", "territorial_share").denominator == 3


def test_second_half_uses_reversed_attack_direction(metadata, make_event):
    events = (
        make_event(kind="shot", occurred_second=2800, available_second=2800, period=2, start={"x": 10, "y": 34}),
        make_event(sequence=2, kind="recovery", occurred_second=2810, available_second=2810, period=2, start={"x": 20, "y": 34}),
    )
    facts = compute_facts(build_snapshot(events, 2, metadata), 0, 2)
    assert get(facts, "a", "shot_quality_total").value == 80
    assert get(facts, "a", "high_recoveries").value == 1


def test_sequence_window_is_exclusive_inclusive(metadata, make_event):
    events = tuple(make_event(sequence=i, kind="shot") for i in (1, 2, 3))
    facts = compute_facts(build_snapshot(events, 3, metadata), 1, 2)
    assert get(facts, "a", "shots").value == 1
    assert get(facts, "a", "shots").event_ids == ("e2",)


def test_late_shot_is_counted_in_its_occurrence_window_only_when_known(metadata, make_event):
    events = (make_event(), make_event(sequence=2, kind="shot", occurred_second=20, available_second=60))
    snapshot = build_snapshot(events, 2, metadata)
    facts = compute_facts(snapshot, 0, 2, start_second=10, end_second=30)
    assert get(facts, "a", "shots").value == 1
    assert get(facts, "a", "shots").interval.end_second == 30
    earlier = compute_facts(build_snapshot(events, 1, metadata), 0, 1)
    assert get(earlier, "a", "shots").value == 0


def test_annulled_events_are_removed_from_values_but_preserved_as_evidence(metadata, make_event):
    events = (make_event(kind="shot"), make_event(sequence=2, kind="goal"),
              make_event(sequence=3, kind="correction"))
    facts = compute_facts(build_snapshot(events, 3, metadata), 0, 2)
    assert get(facts, "a", "shots").value == 0
    assert get(facts, "a", "goals").value == 0
    assert get(facts, "a", "shots").event_ids == ("e1", "e2", "e3")


def test_no_attempts_is_undefined_not_zero_accuracy(metadata):
    facts = compute_facts(build_snapshot((), 0, metadata), 0, 0)
    assert get(facts, "a", "shots").value == 0
    assert get(facts, "a", "pass_accuracy").value is None
    assert get(facts, "a", "territorial_share").value is None


@pytest.mark.parametrize("start,end", [(-1, 1), (2, 1), (0, 2)])
def test_metrics_refuse_invalid_or_future_intervals(metadata, make_event, start, end):
    with pytest.raises(ValueError):
        compute_facts(build_snapshot((make_event(),), 1, metadata), start, end)
