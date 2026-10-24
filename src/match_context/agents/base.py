from dataclasses import dataclass, field
import time
from typing import Literal, Protocol, TYPE_CHECKING

from pydantic import Field

from match_context.domain.contracts import AgentTrace, Claim, TraceStep
from match_context.domain.events import FrozenModel

if TYPE_CHECKING:
    from .tools import ScopedTools


class AgentLimits(FrozenModel):
    model_calls: int = Field(default=7, ge=1, le=7, strict=True)
    tool_calls: int = Field(default=8, ge=1, le=8, strict=True)
    output_tokens: int = Field(default=1200, ge=1, le=1200, strict=True)
    deadline_seconds: float = Field(default=10, gt=0, le=10)


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class RunBudget:
    limits: AgentLimits = field(default_factory=AgentLimits)
    started: float = field(default_factory=time.perf_counter)
    model_calls: int = 0
    tool_names: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    steps: list[TraceStep] = field(default_factory=list)

    def remaining(self) -> float:
        remaining = self.limits.deadline_seconds - (time.perf_counter() - self.started)
        if remaining <= 0:
            raise TimeoutError("deadline")
        return remaining

    def reserve_model(self):
        self.remaining()
        if self.model_calls >= self.limits.model_calls:
            raise BudgetExceeded("model_budget")
        self.model_calls += 1

    def reserve_tool(self, name):
        self.remaining()
        if len(self.tool_names) >= self.limits.tool_calls:
            raise BudgetExceeded("tool_budget")
        self.tool_names.append(name)

    def trace(self) -> AgentTrace:
        return AgentTrace(steps=tuple(self.steps), tool_names=tuple(self.tool_names),
                          model_calls=self.model_calls, tool_calls=len(self.tool_names),
                          input_tokens=self.input_tokens, output_tokens=self.output_tokens,
                          elapsed_seconds=round(time.perf_counter() - self.started, 4))


class CardDraft(FrozenModel):
    story_id: str
    headline: Claim
    explanation: Claim
    suggested_line: Claim
    overlay: Claim

    def claims(self):
        return self.headline, self.explanation, self.suggested_line, self.overlay


class ReviewDecision(FrozenModel):
    story_id: str
    accepted: bool = Field(strict=True)
    codes: tuple[Literal["unsupported_meaning", "wrong_language", "wrong_audience",
                         "causal_language", "missing_limitation", "invalid_output"], ...] = ()


class AgentOutput(FrozenModel):
    selected_story_ids: tuple[str, ...] = Field(default=(), max_length=3)
    cards: tuple[CardDraft, ...] = Field(default=(), max_length=3)
    decisions: tuple[ReviewDecision, ...] = Field(default=(), max_length=3)


class ValidationReport(FrozenModel):
    accepted: tuple[str, ...] = ()
    rejected: tuple[str, ...] = ()
    codes: tuple[str, ...] = ()


class AgentRunner(Protocol):
    mode: str

    async def run(self, role: str, payload: dict, tools: "ScopedTools") -> AgentOutput: ...
