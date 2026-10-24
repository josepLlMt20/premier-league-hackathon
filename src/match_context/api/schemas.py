from typing import Literal

from pydantic import Field
from match_context.domain.events import FrozenModel, Identifier, MatchEvent, MatchMetadata
from match_context.domain.contracts import MetricFact, TeamScore


class ErrorDetail(FrozenModel):
    code: str


class ErrorResponse(FrozenModel):
    error: ErrorDetail


class Health(FrozenModel):
    status: Literal["ok"] = "ok"


class MatchHead(FrozenModel):
    match_id: Identifier
    sequence: int
    available_second: int
    ingestion_state: Literal["external", "running", "complete", "failed"] = "external"


class ResolvedCursor(FrozenModel):
    match_id: Identifier
    available_second: int
    to_sequence: int
    last_event_second: int


class MatchView(FrozenModel):
    match_id: Identifier
    cutoff_sequence: int
    snapshot_id: str
    available_second: int
    metadata: MatchMetadata
    score: tuple[TeamScore, ...]
    recent_events: tuple[MatchEvent, ...] = Field(max_length=100)
    facts: tuple[MetricFact, ...]
    annulled_event_ids: tuple[str, ...]


class EvidenceRequest(FrozenModel):
    match_id: Identifier
    to_sequence: int = Field(ge=0, le=999_999_999_999, strict=True)
    event_ids: tuple[Identifier, ...] = Field(max_length=100)
