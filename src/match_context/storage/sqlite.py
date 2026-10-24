from contextlib import contextmanager
from pathlib import Path
import sqlite3
from threading import RLock

from match_context.domain.events import MatchEvent, MatchMetadata
from .base import EventConflict, EventLog, IngestPosition, MatchNotFound, check_integer, prepare_append


class SQLiteEventLog(EventLog):
    def __init__(self, path: str | Path):
        self._lock = RLock()
        self._connection = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.executescript("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY, metadata TEXT NOT NULL,
                head INTEGER NOT NULL DEFAULT 0, clock INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS events (
                match_id TEXT NOT NULL REFERENCES matches(match_id), sequence INTEGER NOT NULL,
                event_id TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY (match_id, sequence), UNIQUE (match_id, event_id)
            );
        """)

    @contextmanager
    def _transaction(self):
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                yield
                self._connection.commit()
            except BaseException:
                self._connection.rollback()
                raise

    def _header(self, match_id):
        row = self._connection.execute(
            "SELECT metadata, head, clock FROM matches WHERE match_id = ?", (match_id,)).fetchone()
        if row is None:
            raise MatchNotFound(match_id)
        return row

    def register_match(self, metadata: MatchMetadata) -> bool:
        metadata = MatchMetadata.model_validate(metadata.model_dump())
        with self._transaction():
            row = self._connection.execute(
                "SELECT metadata FROM matches WHERE match_id = ?", (metadata.match_id,)).fetchone()
            if row is not None:
                if MatchMetadata.model_validate_json(row[0]) != metadata:
                    raise EventConflict("Match metadata is immutable")
                return False
            self._connection.execute("INSERT INTO matches(match_id, metadata) VALUES (?, ?)",
                                     (metadata.match_id, metadata.model_dump_json()))
        return True

    def metadata(self, match_id: str) -> MatchMetadata:
        with self._lock:
            return MatchMetadata.model_validate_json(self._header(match_id)[0])

    def list_matches(self) -> tuple[MatchMetadata, ...]:
        with self._lock:
            rows = self._connection.execute("SELECT metadata FROM matches ORDER BY match_id").fetchall()
            return tuple(MatchMetadata.model_validate_json(row[0]) for row in rows)

    def position(self, match_id: str) -> IngestPosition:
        with self._lock:
            _, head, clock = self._header(match_id)
            return IngestPosition(head, clock)

    def read_through(self, match_id: str, cutoff: int) -> tuple[MatchEvent, ...]:
        check_integer(cutoff)
        with self._lock:
            _, head, _ = self._header(match_id)
            rows = self._connection.execute(
                "SELECT payload FROM events WHERE match_id = ? AND sequence <= ? ORDER BY sequence",
                (match_id, min(cutoff, head))).fetchall()
            return tuple(MatchEvent.model_validate_json(row[0]) for row in rows)

    def append(self, event: MatchEvent) -> bool:
        with self._transaction():
            raw_metadata, head, clock = self._header(event.match_id)
            prefix = self.read_through(event.match_id, head)
            if not prepare_append(event, MatchMetadata.model_validate_json(raw_metadata),
                                  prefix, IngestPosition(head, clock)):
                return False
            self._connection.execute("INSERT INTO events VALUES (?, ?, ?, ?)",
                                     (event.match_id, event.sequence, event.event_id, event.model_dump_json()))
            self._connection.execute("UPDATE matches SET head = ?, clock = ? WHERE match_id = ?",
                                     (event.sequence, event.available_second, event.match_id))
        return True

    def advance_clock(self, match_id: str, available_second: int) -> None:
        check_integer(available_second, 5400)
        with self._transaction():
            _, _, clock = self._header(match_id)
            if available_second < clock:
                raise ValueError("Ingestion clock cannot rewind")
            self._connection.execute("UPDATE matches SET clock = ? WHERE match_id = ?",
                                     (available_second, match_id))

    def close(self) -> None:
        with self._lock:
            self._connection.close()
