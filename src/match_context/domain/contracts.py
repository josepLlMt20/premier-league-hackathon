from typing import Literal

from pydantic import Field, model_validator

from match_context.domain.events import FrozenModel, Identifier, MatchEvent, MatchMetadata


class ContextRequest(FrozenModel):
    match_id: Identifier
    from_sequence: int = Field(ge=0, strict=True)
    to_sequence: int = Field(ge=0, strict=True)
    role: Literal["fan", "commentator"] = "fan"
    depth: Literal["simple", "detailed"] = "simple"
    language: Literal["es", "en"] = "es"
    favorite_team_id: Identifier | None = None

    @model_validator(mode="after")
    def ordered_interval(self):
        if self.from_sequence > self.to_sequence:
            raise ValueError("Interval start cannot exceed its end")
        return self


class TeamScore(FrozenModel):
    team_id: Identifier
    goals: int = Field(ge=0)


class BoundedSnapshot(FrozenModel):
    metadata: MatchMetadata
    cutoff: int = Field(ge=0)
    cutoff_second: int = Field(ge=0, le=5400)
    known_events: tuple[MatchEvent, ...]
    effective_events: tuple[MatchEvent, ...]
    annulled_event_ids: tuple[str, ...]
    score: tuple[TeamScore, ...]
    prefix_hash: str

    @property
    def snapshot_id(self) -> str:
        return f"{self.metadata.match_id}:{self.cutoff}:{self.prefix_hash[:16]}"


class FactInterval(FrozenModel):
    start_sequence: int = Field(ge=0)
    end_sequence: int = Field(ge=0)
    start_second: int | None = Field(default=None, ge=0, le=5400)
    end_second: int | None = Field(default=None, ge=0, le=5400)

    @model_validator(mode="after")
    def ordered_bounds(self):
        if self.end_sequence < self.start_sequence:
            raise ValueError("Sequence interval is reversed")
        if (self.start_second is None) != (self.end_second is None):
            raise ValueError("Both occurred-time bounds are required")
        if self.start_second is not None and self.end_second < self.start_second:
            raise ValueError("Time interval is reversed")
        return self


class MetricFact(FrozenModel):
    fact_id: str
    snapshot_id: str
    cutoff_sequence: int
    team_id: Identifier
    name: str
    value: int | float | None
    unit: str
    interval: FactInterval
    denominator: int | None = Field(default=None, ge=0)
    sample_count: int = Field(ge=0)
    event_ids: tuple[str, ...]
    method: str
    limitations: tuple[str, ...] = ()


class EvidenceBundle(FrozenModel):
    snapshot_id: str
    cutoff_sequence: int
    events: tuple[MatchEvent, ...]
    annulled_event_ids: tuple[str, ...]


class StoryCandidate(FrozenModel):
    story_id: str
    pattern: Literal["high_recoveries", "chance_quality", "territorial_shift"]
    team_id: Identifier
    priority: float
    delta: float
    current_interval: FactInterval
    comparison_interval: FactInterval
    fact_ids: tuple[str, ...]
    event_ids: tuple[str, ...]
    limitations: tuple[str, ...]


class Claim(FrozenModel):
    claim_id: Identifier
    kind: Literal["observed", "interpretation"]
    text: str = Field(min_length=1, max_length=600)
    fact_ids: tuple[str, ...] = Field(default=(), max_length=12)
    event_ids: tuple[str, ...] = Field(default=(), max_length=10)
    limitations: tuple[str, ...] = Field(default=(), max_length=3)


class ContextCard(FrozenModel):
    story_id: str
    headline: str
    explanation: str
    suggested_line: str
    overlay_text: str = Field(max_length=140)
    claims: tuple[Claim, ...]
    current_interval: FactInterval
    comparison_interval: FactInterval
    limitations: tuple[str, ...]


class TraceStep(FrozenModel):
    role: Literal["analyst", "writer", "reviewer", "system"]
    decision: str


class AgentTrace(FrozenModel):
    steps: tuple[TraceStep, ...] = ()
    tool_names: tuple[str, ...] = ()
    model_calls: int = Field(default=0, ge=0)
    tool_calls: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    elapsed_seconds: float = Field(default=0, ge=0)


class ContextResult(FrozenModel):
    request: ContextRequest
    snapshot_id: str
    status: Literal["verified", "factual", "insufficient"]
    mode: Literal["foundry", "scripted", "factual"]
    summary: str
    summary_claims: tuple[Claim, ...] = ()
    cards: tuple[ContextCard, ...] = Field(default=(), max_length=3)
    facts: tuple[MetricFact, ...]
    evidence_ids: tuple[str, ...] = ()
    rejection_codes: tuple[str, ...] = ()
    trace_id: str
    trace: AgentTrace = Field(default_factory=AgentTrace)
