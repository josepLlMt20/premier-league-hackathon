import pytest

from match_context.analysis.snapshot import build_snapshot
from match_context.analysis.patterns import detect_stories
from match_context.analysis.evidence import resolve_evidence
from match_context.domain.contracts import ContextRequest


def snapshot_at(match, second):
    cutoff = max((event.sequence for event in match.events if event.available_second <= second), default=0)
    return build_snapshot(match.events, cutoff, match.metadata)


def request_for(snapshot, **kwargs):
    data = {"match_id": snapshot.metadata.match_id, "from_sequence": 0, "to_sequence": snapshot.cutoff}
    data.update(kwargs)
    return ContextRequest(**data)


def test_main_recovers_introduced_patterns_with_auditable_comparisons(scenario_main):
    snapshot = snapshot_at(scenario_main, 1500)
    stories = detect_stories(snapshot, request_for(snapshot))
    high = next(story for story in stories if story.pattern == "high_recoveries")
    chances = next(story for story in stories if story.pattern == "chance_quality")
    assert high.team_id == "amber"
    assert high.delta == 3
    assert high.current_interval.start_second == 1200
    assert high.current_interval.end_second == 1500
    assert high.comparison_interval.start_second == 900
    assert high.comparison_interval.end_second == 1200
    assert chances.delta >= 30
    for story in stories:
        evidence = resolve_evidence(snapshot, story.event_ids)
        assert evidence.events
        assert max(event.sequence for event in evidence.events) <= snapshot.cutoff
        assert story.fact_ids
        assert story.limitations


@pytest.mark.parametrize("second", [600, 1200, 1500, 2700, 5400])
def test_neutral_match_does_not_manufacture_a_change(scenario_neutral, second):
    snapshot = snapshot_at(scenario_neutral, second)
    assert detect_stories(snapshot, request_for(snapshot)) == ()


def test_sterile_control_does_not_become_an_attacking_threat(scenario_sterile):
    snapshot = snapshot_at(scenario_sterile, 1500)
    stories = detect_stories(snapshot, request_for(snapshot, from_sequence=1))
    assert any(story.pattern == "territorial_shift" and story.team_id == "amber" for story in stories)
    assert not any(story.pattern == "chance_quality" for story in stories)


def test_favorite_changes_no_fact_ids_or_observations(scenario_main):
    snapshot = snapshot_at(scenario_main, 1500)
    plain = detect_stories(snapshot, request_for(snapshot))
    preferred = detect_stories(snapshot, request_for(snapshot, favorite_team_id="cobalt"))
    observations = lambda stories: {(s.story_id, s.delta, s.fact_ids, s.event_ids) for s in stories}
    assert observations(plain) == observations(preferred)
    assert detect_stories(snapshot, request_for(snapshot)) == plain


def test_empty_early_and_sparse_windows_have_no_trend(metadata, make_event):
    for events in ((), (make_event(),), (make_event(occurred_second=1200, available_second=1200),)):
        snapshot = build_snapshot(events, len(events), metadata)
        assert detect_stories(snapshot, request_for(snapshot)) == ()


def test_empty_requested_interval_has_no_story(scenario_main):
    snapshot = snapshot_at(scenario_main, 1500)
    request = ContextRequest(match_id=snapshot.metadata.match_id, from_sequence=snapshot.cutoff,
                             to_sequence=snapshot.cutoff)
    assert detect_stories(snapshot, request) == ()


def test_overlapping_windows_do_not_repeat_the_same_shooting_episode(scenario_correction):
    snapshot = snapshot_at(scenario_correction, 1600)
    stories = detect_stories(snapshot, request_for(snapshot))
    assert sum(story.pattern == "chance_quality" and story.team_id == "amber" for story in stories) == 1


def test_snapshot_must_match_request_knowledge_boundary(scenario_main):
    snapshot = snapshot_at(scenario_main, 1500)
    with pytest.raises(ValueError):
        detect_stories(snapshot, ContextRequest(match_id=snapshot.metadata.match_id,
                       from_sequence=0, to_sequence=snapshot.cutoff - 1))
    with pytest.raises(ValueError):
        detect_stories(snapshot, request_for(snapshot, favorite_team_id="unknown"))


def test_detection_includes_exact_thresholds_and_real_comparison_denominators(metadata, make_event):
    rows = []
    def append(second, team="a", kind="pass", **kwargs):
        attributes = {"recipient_id": f"{team}2", "completed": True} if kind == "pass" else {}
        attributes.update(kwargs.pop("attributes", {}))
        rows.append(make_event(sequence=len(rows)+1, kind=kind, team_id=team, player_id=f"{team}1",
                    occurred_second=second, available_second=second, attributes=attributes, **kwargs))
    for index in range(10):
        team = "a" if index < 6 else "b"
        append(10 + index * 20, team, end={"x": 80 if team == "a" else 20, "y": 34})
    append(300, kind="pressure")
    for index in range(10):
        team = "a" if index < 8 else "b"
        append(310 + index * 10, team, end={"x": 80 if team == "a" else 20, "y": 34})
    append(420, kind="recovery", start={"x": 70, "y": 34})
    append(430, kind="recovery", start={"x": 70, "y": 34})
    for second in (440, 450):
        append(second, kind="shot", start={"x": 62.5, "y": 34}, attributes={"on_target": False})
    append(600, kind="pressure")
    snapshot = build_snapshot(tuple(rows), len(rows), metadata)
    stories = detect_stories(snapshot, request_for(snapshot))
    assert {story.pattern: story.delta for story in stories} == {
        "high_recoveries": 2, "chance_quality": 30, "territorial_shift": 20,
    }


def test_new_sequences_in_the_same_arrival_second_are_not_an_empty_interval(metadata, make_event):
    rows = []
    for second in list(range(10, 210, 20)) + [300] + list(range(310, 410, 10)) + [600]:
        rows.append(make_event(sequence=len(rows)+1, occurred_second=second, available_second=second))
    start = len(rows)
    for kind in ("recovery", "recovery", "shot", "shot"):
        rows.append(make_event(sequence=len(rows)+1, kind=kind, occurred_second=600, available_second=600,
            start={"x": 70 if kind == "recovery" else 62.5, "y": 34}))
    snapshot = build_snapshot(tuple(rows), len(rows), metadata)
    request = ContextRequest(match_id=metadata.match_id, from_sequence=start, to_sequence=len(rows))
    stories = detect_stories(snapshot, request)
    assert {story.pattern: story.delta for story in stories} == {"high_recoveries": 2, "chance_quality": 30}


def test_tied_candidates_have_stable_order_and_preference_only_changes_ranking(metadata, make_event):
    rows = []
    for second in list(range(10, 210, 20)) + [300] + list(range(310, 410, 10)):
        rows.append(make_event(sequence=len(rows)+1, occurred_second=second, available_second=second))
    for index, team in enumerate(("a", "a", "b", "b")):
        second = 420 + index * 10
        rows.append(make_event(sequence=len(rows)+1, kind="recovery", team_id=team, player_id=team+"1",
            occurred_second=second, available_second=second, start={"x": 70 if team == "a" else 20, "y": 34}))
    rows.append(make_event(sequence=len(rows)+1, kind="pressure", occurred_second=600, available_second=600))
    snapshot = build_snapshot(tuple(rows), len(rows), metadata)
    plain = detect_stories(snapshot, request_for(snapshot))
    favored = detect_stories(snapshot, request_for(snapshot, favorite_team_id="b"))
    assert [story.team_id for story in plain] == ["a", "b"]
    assert [story.team_id for story in favored] == ["b", "a"]
    assert {(s.story_id, s.delta, s.fact_ids, s.event_ids) for s in plain} == {
        (s.story_id, s.delta, s.fact_ids, s.event_ids) for s in favored
    }
