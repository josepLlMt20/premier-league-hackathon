from dataclasses import dataclass
import math
from threading import RLock

from match_context.domain.events import GeneratedMatch
from match_context.storage.base import EventConflict, EventLog, IngestPosition, MatchNotFound, check_integer


class IngestionFailed(RuntimeError):
    """The shared stream is stopped at its last confirmed durable position."""


@dataclass(frozen=True)
class IngestStatus:
    match_id: str
    sequence: int
    available_second: int
    state: str
    error_type: str | None = None


class Ingestor:
    """Single shared writer driven by elapsed wall time or an explicit match clock.

    A viewer's pause, seek or playback rate must never call this writer. A server
    scheduler owns it; each match advances independently from its durable header.
    """

    def __init__(self, log: EventLog, matches: tuple[GeneratedMatch, ...], *, speed: float = 30):
        self._check_elapsed(speed, positive=True)
        self.speed = speed
        self._log = log
        self._lock = RLock()
        self._matches = {}
        self._failed: dict[str, str] = {}
        self._confirmed: dict[str, IngestPosition] = {}
        self._fraction: dict[str, float] = {}
        for source in matches:
            match = GeneratedMatch.model_validate(source.model_dump())
            match_id = match.metadata.match_id
            if match_id in self._matches:
                raise ValueError("Duplicate match source")
            self._log.register_match(match.metadata)
            self._matches[match_id] = match
            self._check_source(match_id)

    @staticmethod
    def _check_elapsed(value, *, positive=False):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or positive and value == 0:
            raise ValueError("Expected a finite positive rate or non-negative elapsed time")

    def _match(self, match_id):
        try:
            return self._matches[match_id]
        except KeyError as error:
            raise MatchNotFound(match_id) from error

    def _position(self, match_id):
        try:
            return self._log.position(match_id)
        except Exception as error:
            self._failed[match_id] = type(error).__name__
            self._fraction[match_id] = 0
            raise IngestionFailed("Cannot read durable position; ingestion stopped") from error

    def _check_source(self, match_id):
        match = self._match(match_id)
        position = self._log.position(match_id)
        if self._log.read_through(match_id, position.sequence) != match.events[:position.sequence]:
            raise EventConflict("Replay source differs from committed history")
        next_events = match.events[position.sequence:]
        # Equality is allowed: an interrupted tick may have committed only some
        # events from the same availability second.
        if next_events and next_events[0].available_second < position.available_second:
            raise EventConflict("Replay source inserts events behind the durable clock")
        self._confirmed[match_id] = position

    def tick(self, match_id: str, available_second: int) -> int:
        check_integer(available_second, 5400)
        with self._lock:
            result = self._tick(match_id, available_second)
            self._fraction[match_id] = 0
            return result

    def _tick(self, match_id, available_second):
        match = self._match(match_id)
        if match_id in self._failed:
            raise IngestionFailed("Resume ingestion explicitly before retrying")
        position = self._position(match_id)
        if available_second < position.available_second:
            raise ValueError("Shared ingestion cannot rewind")
        added = 0
        try:
            for event in match.events[position.sequence:]:
                if event.available_second > available_second:
                    break
                added += self._log.append(event)
                self._confirmed[match_id] = IngestPosition(event.sequence, event.available_second)
            self._log.advance_clock(match_id, available_second)
            self._confirmed[match_id] = self._log.position(match_id)
        except Exception as error:
            self._failed[match_id] = type(error).__name__
            self._fraction[match_id] = 0
            raise IngestionFailed("Ingestion stopped; committed history is retained") from error
        return added

    def advance(self, match_id: str, elapsed_seconds: float) -> int:
        self._check_elapsed(elapsed_seconds)
        with self._lock:
            self._match(match_id)
            position = self._position(match_id)
            target = min(5400, position.available_second + self._fraction.get(match_id, 0)
                         + elapsed_seconds * self.speed)
            result = self._tick(match_id, math.floor(target))
            self._fraction[match_id] = target - math.floor(target)
            return result

    def resume(self, match_id: str) -> None:
        with self._lock:
            self._check_source(match_id)
            self._failed.pop(match_id, None)
            self._fraction[match_id] = 0

    def status(self, match_id: str) -> IngestStatus:
        with self._lock:
            self._match(match_id)
            if match_id in self._failed:
                position = self._confirmed[match_id]
                return IngestStatus(match_id, position.sequence, position.available_second,
                                    "failed", self._failed[match_id])
            position = self._position(match_id)
            complete = (position.available_second == 5400
                        and position.sequence == len(self._match(match_id).events))
            return IngestStatus(match_id, position.sequence, position.available_second,
                                "complete" if complete else "running")
