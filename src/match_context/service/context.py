import asyncio
import time

from match_context.agents.base import AgentLimits, AgentRunner
from match_context.agents.fallback import build_factual_result
from match_context.agents.orchestrator import orchestrate, prepare_tools
from match_context.analysis.evidence import resolve_evidence
from match_context.analysis.metrics import compute_facts
from match_context.analysis.snapshot import build_snapshot
from match_context.config import Settings
from match_context.domain.contracts import ContextRequest, ContextResult
from match_context.storage.base import EventLog, MatchNotFound, check_integer
from .cache import ContextCache


class ServiceError(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)


class ContextService:
    def __init__(self, settings: Settings, log: EventLog, runner: AgentRunner | None = None):
        if runner is not None and runner.mode != settings.agent_mode:
            raise ValueError("Runner and configured mode must match")
        if settings.agent_mode == "scripted" and runner is None:
            raise ValueError("Scripted mode requires an explicitly injected runner")
        self.settings, self.log, self.runner = settings, log, runner
        self.cache: ContextCache[ContextResult] = ContextCache(capacity=settings.cache_capacity)
        self._active = 0
        self._slots_lock = asyncio.Lock()

    async def read(self, function, *args):
        try:
            return await asyncio.wait_for(asyncio.to_thread(function, *args),
                                          timeout=self.settings.context_timeout_seconds)
        except ServiceError:
            raise
        except MatchNotFound:
            raise ServiceError(404, "match_not_found") from None
        except TimeoutError:
            raise ServiceError(503, "storage_timeout") from None
        except Exception:
            raise ServiceError(503, "storage_unavailable") from None

    def _snapshot(self, match_id, cutoff):
        try:
            check_integer(cutoff)
        except ValueError:
            raise ServiceError(422, "invalid_cutoff") from None
        position = self.log.position(match_id)
        if cutoff > position.sequence:
            raise ServiceError(422, "future_cutoff")
        metadata = self.log.metadata(match_id)
        return build_snapshot(self.log.read_through(match_id, cutoff), cutoff, metadata)

    async def snapshot(self, match_id, cutoff):
        return await self.read(self._snapshot, match_id, cutoff)

    def _cursor(self, match_id, second):
        position = self.log.position(match_id)
        if second > position.available_second:
            raise ServiceError(422, "future_time")
        prefix = self.log.read_through(match_id, position.sequence)
        available = [event for event in prefix if event.available_second <= second]
        return {"match_id": match_id, "available_second": second,
                "to_sequence": available[-1].sequence if available else 0,
                "last_event_second": available[-1].available_second if available else 0}

    async def cursor(self, match_id, second):
        return await self.read(self._cursor, match_id, second)

    async def view(self, match_id, cutoff):
        def reconstruct():
            snapshot = self._snapshot(match_id, cutoff)
            return {"match_id": match_id, "cutoff_sequence": cutoff, "snapshot_id": snapshot.snapshot_id,
                    "available_second": snapshot.cutoff_second, "metadata": snapshot.metadata,
                    "score": snapshot.score, "recent_events": snapshot.known_events[-100:],
                    "facts": compute_facts(snapshot, 0, cutoff), "annulled_event_ids": snapshot.annulled_event_ids}
        return await self.read(reconstruct)

    async def evidence(self, request):
        def resolve():
            snapshot = self._snapshot(request.match_id, request.to_sequence)
            try:
                return resolve_evidence(snapshot, request.event_ids)
            except ValueError:
                raise ServiceError(422, "unknown_evidence") from None
        return await self.read(resolve)

    async def get_context(self, request: ContextRequest) -> ContextResult:
        started = time.perf_counter()
        snapshot = await self.snapshot(request.match_id, request.to_sequence)
        if request.favorite_team_id is not None and request.favorite_team_id not in {
                team.team_id for team in snapshot.metadata.teams}:
            raise ServiceError(422, "unknown_favorite")
        key = self.cache.key(request, snapshot.prefix_hash)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        if self.settings.agent_mode == "factual" or self.runner is None:
            tools = prepare_tools(snapshot, request)
            result = build_factual_result(snapshot, request, tools.facts, tools=tools,
                rejection_codes=() if self.settings.agent_mode == "factual" else ("provider_unavailable",))
            if self.settings.agent_mode == "factual":
                self.cache.put(key, result)
            return result

        async with self._slots_lock:
            if self._active >= self.settings.max_concurrent_generations:
                raise ServiceError(429, "generation_busy")
            self._active += 1
        try:
            remaining = self.settings.context_timeout_seconds - (time.perf_counter() - started)
            if remaining <= 0:
                tools = prepare_tools(snapshot, request)
                return build_factual_result(snapshot, request, tools.facts, tools=tools, rejection_codes=("deadline",))
            limits = AgentLimits(model_calls=self.settings.max_model_calls, tool_calls=self.settings.max_tool_calls,
                                 output_tokens=self.settings.max_output_tokens, deadline_seconds=remaining)
            result = await orchestrate(snapshot, request, self.runner, limits=limits)
            # A transient provider failure must not poison future requests.
            if result.status == "verified":
                self.cache.put(key, result)
            return result
        finally:
            async with self._slots_lock:
                self._active -= 1
