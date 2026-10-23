import sqlite3

import pytest

from match_context.storage.base import EventConflict, MatchNotFound
from match_context.storage.sqlite import SQLiteEventLog


def test_duplicate_and_conflict_leave_the_original_history(log_factory, metadata, make_event):
    log = log_factory()
    log.register_match(metadata)
    first = make_event()
    assert log.append(first) is True
    assert log.append(first) is False
    for conflicting in (first.model_copy(update={"end": first.start}),
                        first.model_copy(update={"event_id": "other"})):
        with pytest.raises(EventConflict):
            log.append(conflicting)
    assert log.head("match-1") == 1
    assert log.read_through("match-1", 1) == (first,)


def test_restart_retains_metadata_prefix_and_clock(log_factory, metadata, make_event):
    first = log_factory()
    first.register_match(metadata)
    first.append(make_event())
    first.advance_clock("match-1", 19)
    first.close()
    second = log_factory()
    assert second.metadata("match-1") == metadata
    assert second.position("match-1").sequence == 1
    assert second.position("match-1").available_second == 19
    assert second.read_through("match-1", 1) == (make_event(),)
    assert second.append(make_event(sequence=2)) is True


def test_registration_is_idempotent_but_metadata_cannot_change(log_factory, metadata):
    log = log_factory()
    assert log.register_match(metadata) is True
    assert log.register_match(metadata) is False
    changed_team = metadata.teams[0].model_copy(update={"name": "Changed"})
    changed = metadata.model_copy(update={"teams": (changed_team, metadata.teams[1])})
    with pytest.raises(EventConflict):
        log.register_match(changed)
    assert log.metadata("match-1") == metadata


def test_reads_are_ordered_bounded_and_partitioned(log_factory, metadata, make_event):
    log = log_factory()
    log.register_match(metadata)
    other = metadata.model_copy(update={"match_id": "match-2"})
    log.register_match(other)
    log.append(make_event(match_id="match-2"))
    for sequence in range(1, 13):
        log.append(make_event(sequence=sequence))
    assert [e.sequence for e in log.read_through("match-1", 10)] == list(range(1, 11))
    assert log.read_through("match-1", 0) == ()
    assert log.head("match-1") == 12
    assert log.head("match-2") == 1


@pytest.mark.parametrize("change", [
    {"sequence": 2}, {"team_id": "outsider"}, {"player_id": "b1"},
    {"available_second": -1}, {"kind": "goal"},
])
def test_invalid_event_does_not_advance_header(log_factory, metadata, make_event, change):
    log = log_factory()
    log.register_match(metadata)
    with pytest.raises(ValueError):
        log.append(make_event().model_copy(update=change))
    assert log.head("match-1") == 0
    assert log.position("match-1").available_second == 0


def test_reused_event_id_at_another_sequence_is_rejected(log_factory, metadata, make_event):
    log = log_factory()
    log.register_match(metadata)
    log.append(make_event())
    with pytest.raises(EventConflict):
        log.append(make_event(sequence=2, event_id="e1"))
    assert log.head("match-1") == 1


def test_independent_writers_observe_the_same_committed_history(log_factory, metadata, make_event):
    first, second = log_factory(), log_factory()
    first.register_match(metadata)
    assert first.append(make_event()) is True
    assert second.append(make_event()) is False
    assert second.append(make_event(sequence=2)) is True
    assert first.head("match-1") == 2
    assert [e.event_id for e in first.read_through("match-1", 2)] == ["e1", "e2"]


def test_clock_cannot_rewind_and_events_cannot_fill_a_committed_gap(log_factory, metadata, make_event):
    log = log_factory()
    log.register_match(metadata)
    log.advance_clock("match-1", 11)
    with pytest.raises(ValueError):
        log.advance_clock("match-1", 10)
    with pytest.raises(ValueError):
        log.append(make_event())
    assert log.head("match-1") == 0
    assert log.position("match-1").available_second == 11


@pytest.mark.parametrize("cutoff", [-1, True, 1.5])
def test_invalid_cutoffs_are_rejected(log_factory, metadata, cutoff):
    log = log_factory()
    log.register_match(metadata)
    with pytest.raises(ValueError):
        log.read_through("match-1", cutoff)


def test_unknown_matches_do_not_silently_become_empty(log_factory, make_event):
    log = log_factory()
    with pytest.raises(MatchNotFound):
        log.head("match-1")
    with pytest.raises(MatchNotFound):
        log.read_through("match-1", 0)
    with pytest.raises(MatchNotFound):
        log.append(make_event())


def test_sqlite_rolls_back_event_if_header_update_fails(tmp_path, metadata, make_event):
    path = tmp_path / "atomic.sqlite3"
    log = SQLiteEventLog(path)
    log.register_match(metadata)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TRIGGER reject_header BEFORE UPDATE ON matches BEGIN SELECT RAISE(ABORT, 'disk failure'); END")
    with pytest.raises(sqlite3.DatabaseError):
        log.append(make_event())
    assert log.head("match-1") == 0
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
    log.close()


def test_sqlite_commit_failure_rolls_back_and_same_writer_can_resume(tmp_path, metadata, make_event):
    from match_context.domain.events import GeneratedMatch
    from match_context.simulation.ingest import IngestionFailed, Ingestor

    path = tmp_path / "busy.sqlite3"
    log = SQLiteEventLog(path)
    writer = Ingestor(log, (GeneratedMatch(metadata=metadata, events=(make_event(),)),))
    log._connection.execute("PRAGMA busy_timeout = 20")
    reader = sqlite3.connect(path, isolation_level=None)
    try:
        reader.execute("BEGIN")
        reader.execute("SELECT * FROM matches").fetchall()
        with pytest.raises(IngestionFailed):
            writer.tick("match-1", 10)
        reader.rollback()
        assert log.head("match-1") == 0
        assert log.position("match-1").available_second == 0
        assert not log._connection.in_transaction
        writer.resume("match-1")
        assert writer.tick("match-1", 10) == 1
        assert log.head("match-1") == 1
    finally:
        reader.close()
        log.close()
