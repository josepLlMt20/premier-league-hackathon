from abc import ABC, abstractmethod
from dataclasses import dataclass

from match_context.domain.events import MatchEvent, MatchMetadata, validate_event, validate_stream

MAX_SEQUENCE = 999_999_999_999


class EventConflict(ValueError):
    """An immutable event or match identifier was reused with different data."""


class MatchNotFound(LookupError):
    pass


class ConcurrentWrite(RuntimeError):
    """Another writer changed the header; retry from a fresh durable position."""


class CorruptEventLog(RuntimeError):
    pass


@dataclass(frozen=True)
class IngestPosition:
    sequence: int
    available_second: int


def check_integer(value: int, maximum: int = MAX_SEQUENCE) -> None:
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(f"Expected an integer between 0 and {maximum}")


def prepare_append(event: MatchEvent, metadata: MatchMetadata,
                   prefix: tuple[MatchEvent, ...], position: IngestPosition) -> bool:
    validate_event(event)
    check_integer(event.sequence)
    if event.match_id != metadata.match_id:
        raise ValueError("Event belongs to a different match")
    for previous in prefix:
        if previous.sequence == event.sequence or previous.event_id == event.event_id:
            if previous == event:
                return False
            raise EventConflict("Event identity is already committed with different data")
    if event.available_second < position.available_second:
        raise ValueError("Cannot append behind the committed ingestion clock")
    validate_stream((*prefix, event), metadata)
    return True


class EventLog(ABC):
    """One immutable history per match; read_through returns only its bounded prefix."""

    @abstractmethod
    def register_match(self, metadata: MatchMetadata) -> bool: ...

    @abstractmethod
    def metadata(self, match_id: str) -> MatchMetadata: ...

    @abstractmethod
    def position(self, match_id: str) -> IngestPosition: ...

    def head(self, match_id: str) -> int:
        return self.position(match_id).sequence

    @abstractmethod
    def read_through(self, match_id: str, cutoff: int) -> tuple[MatchEvent, ...]: ...

    @abstractmethod
    def append(self, event: MatchEvent) -> bool: ...

    @abstractmethod
    def advance_clock(self, match_id: str, available_second: int) -> None: ...

    @abstractmethod
    def close(self) -> None: ...
