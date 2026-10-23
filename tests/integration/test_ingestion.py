import pytest

from match_context.analysis.snapshot import build_snapshot
from match_context.domain.events import GeneratedMatch
from match_context.simulation.ingest import IngestionFailed, Ingestor
from match_context.storage.base import EventConflict


def test_tick_receives_only_available_events_and_is_idempotent(log_factory, metadata, make_event):
    log = log_factory()
    match = GeneratedMatch(metadata=metadata, events=tuple(make_event(sequence=i) for i in range(1, 4)))
    ingestor = Ingestor(log, (match,))
    assert ingestor.tick("match-1", 19) == 1
    assert log.read_through("match-1", 99) == (make_event(),)
    assert ingestor.tick("match-1", 19) == 0
    assert ingestor.tick("match-1", 20) == 1
    assert ingestor.status("match-1").sequence == 2
    with pytest.raises(ValueError):
        ingestor.tick("match-1", 18)
    assert log.head("match-1") == 2


def test_restart_continues_from_durable_clock_including_empty_gaps(log_factory, metadata, make_event):
    match = GeneratedMatch(metadata=metadata, events=(make_event(), make_event(sequence=2)))
    first_log = log_factory()
    first = Ingestor(first_log, (match,))
    assert first.tick("match-1", 19) == 1
    first_log.close()
    log = log_factory()
    restarted = Ingestor(log, (match,), speed=2)
    assert restarted.advance("match-1", 0.5) == 1
    assert restarted.status("match-1").available_second == 20
    assert log.head("match-1") == 2


def test_default_speed_and_fractional_steps_do_not_drop_time(log_factory, metadata, make_event):
    log = log_factory()
    match = GeneratedMatch(metadata=metadata, events=(make_event(), make_event(sequence=2)))
    ingestor = Ingestor(log, (match,))
    assert ingestor.advance("match-1", 0.25) == 0
    assert ingestor.status("match-1").available_second == 7
    assert ingestor.advance("match-1", 0.25) == 1
    assert ingestor.status("match-1").available_second == 15
    assert ingestor.advance("match-1", 0.5) == 1
    assert ingestor.status("match-1").available_second == 30


def test_same_second_events_resume_after_partial_failure(log_factory, metadata, make_event, monkeypatch):
    log = log_factory()
    events = (make_event(), make_event(sequence=2, occurred_second=10, available_second=10))
    ingestor = Ingestor(log, (GeneratedMatch(metadata=metadata, events=events),))
    actual_append = log.append

    def interrupted(event):
        if event.sequence == 2:
            raise OSError("storage unavailable")
        return actual_append(event)

    monkeypatch.setattr(log, "append", interrupted)
    with pytest.raises(IngestionFailed):
        ingestor.tick("match-1", 30)
    status = ingestor.status("match-1")
    assert (status.state, status.sequence, status.available_second) == ("failed", 1, 10)
    with pytest.raises(IngestionFailed):
        ingestor.advance("match-1", 1)
    assert log.head("match-1") == 1
    monkeypatch.setattr(log, "append", actual_append)
    ingestor.resume("match-1")
    assert ingestor.tick("match-1", 10) == 1
    assert log.head("match-1") == 2


def test_failure_before_checkpoint_preserves_last_received_event(log_factory, metadata, make_event, monkeypatch):
    log = log_factory()
    match = GeneratedMatch(metadata=metadata, events=(make_event(),))
    ingestor = Ingestor(log, (match,))

    def failed_checkpoint(*args):
        raise OSError("checkpoint unavailable")

    monkeypatch.setattr(log, "advance_clock", failed_checkpoint)
    with pytest.raises(IngestionFailed):
        ingestor.tick("match-1", 19)
    assert log.position("match-1").available_second == 10
    assert ingestor.status("match-1").state == "failed"


@pytest.mark.parametrize("speed", [0, -1, float("inf"), float("nan"), True])
def test_invalid_speed_is_rejected(log_factory, speed):
    with pytest.raises(ValueError):
        Ingestor(log_factory(), (), speed=speed)


def test_completion_caps_clock_at_match_duration(log_factory, metadata, make_event):
    log = log_factory()
    ingestor = Ingestor(log, (GeneratedMatch(metadata=metadata, events=(make_event(),)),))
    ingestor.advance("match-1", 1000)
    assert ingestor.status("match-1").state == "complete"
    assert log.position("match-1").available_second == 5400
    assert ingestor.advance("match-1", 1) == 0


def test_final_second_is_not_complete_until_all_its_events_are_committed(log_factory, metadata, make_event):
    log = log_factory()
    events = tuple(make_event(sequence=i, occurred_second=5400, available_second=5400, period=2)
                   for i in (1, 2))
    match = GeneratedMatch(metadata=metadata, events=events)
    log.register_match(metadata)
    log.append(events[0])
    restarted = Ingestor(log, (match,))
    assert restarted.status("match-1").state == "running"
    assert restarted.tick("match-1", 5400) == 1
    assert restarted.status("match-1").state == "complete"


def test_goal_and_late_annulment_preserve_two_viewer_positions(log_factory, metadata, make_event):
    log = log_factory()
    events = (make_event(kind="shot", occurred_second=1490, available_second=1490),
              make_event(sequence=2, kind="goal", occurred_second=1495, available_second=1495),
              make_event(sequence=3, kind="correction", occurred_second=1495, available_second=1565,
                         player_id=None, attributes={"target_event_id": "e2", "action": "annul"}))
    ingestor = Ingestor(log, (GeneratedMatch(metadata=metadata, events=events),))
    ingestor.tick("match-1", 1490)
    assert [s.goals for s in build_snapshot(log.read_through("match-1", 1), 1, metadata).score] == [0, 0]
    ingestor.tick("match-1", 1500)
    assert [s.goals for s in build_snapshot(log.read_through("match-1", 2), 2, metadata).score] == [1, 0]
    ingestor.tick("match-1", 1600)
    assert [s.goals for s in build_snapshot(log.read_through("match-1", 3), 3, metadata).score] == [0, 0]
    assert [s.goals for s in build_snapshot(log.read_through("match-1", 2), 2, metadata).score] == [1, 0]
    assert len(log.read_through("match-1", 99)) == 3


def test_position_read_failure_stops_ingestion_until_explicit_resume(log_factory, metadata, make_event, monkeypatch):
    log = log_factory()
    ingestor = Ingestor(log, (GeneratedMatch(metadata=metadata, events=(make_event(),)),))
    actual_position = log.position

    def unavailable(*args):
        raise OSError("storage unavailable")

    monkeypatch.setattr(log, "position", unavailable)
    with pytest.raises(IngestionFailed):
        ingestor.advance("match-1", 1)
    assert ingestor.status("match-1").state == "failed"
    assert ingestor.status("match-1").sequence == 0
    monkeypatch.setattr(log, "position", actual_position)
    with pytest.raises(IngestionFailed):
        ingestor.tick("match-1", 30)
    ingestor.resume("match-1")
    assert ingestor.tick("match-1", 30) == 1


def test_restarting_with_changed_source_cannot_rewrite_history(log_factory, metadata, make_event):
    log = log_factory()
    match = GeneratedMatch(metadata=metadata, events=(make_event(),))
    Ingestor(log, (match,)).tick("match-1", 10)
    altered = GeneratedMatch(metadata=metadata, events=(make_event(end={"x": 40, "y": 34}),))
    with pytest.raises(EventConflict):
        Ingestor(log, (altered,))
    assert log.read_through("match-1", 1) == match.events


@pytest.mark.parametrize("elapsed", [-1, float("inf"), float("nan"), True])
def test_invalid_elapsed_time_cannot_advance_clock(log_factory, metadata, elapsed):
    log = log_factory()
    ingestor = Ingestor(log, (GeneratedMatch(metadata=metadata, events=()),))
    with pytest.raises(ValueError):
        ingestor.advance("match-1", elapsed)
    assert log.position("match-1").available_second == 0
