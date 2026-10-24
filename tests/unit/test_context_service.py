import asyncio

import pytest

from match_context.config import Settings
from match_context.domain.contracts import ContextRequest
from match_context.service.context import ContextService
from match_context.simulation.ingest import Ingestor
from match_context.storage.sqlite import SQLiteEventLog
from tests.unit.agent_helpers import ScriptedRunner


@pytest.fixture
def stored(tmp_path, scenario_main):
    log = SQLiteEventLog(tmp_path / "service.sqlite3")
    Ingestor(log, (scenario_main,)).tick(scenario_main.metadata.match_id, 1500)
    yield log, ContextRequest(match_id=scenario_main.metadata.match_id, from_sequence=0, to_sequence=269)
    log.close()


def test_provider_fallback_is_not_cached_and_recovers_on_next_request(stored):
    log, request = stored

    class Recovers(ScriptedRunner):
        mode = "foundry"
        broken = True
        async def run(self, *args):
            if self.broken:
                self.broken = False
                raise RuntimeError("private token and provider endpoint")
            return await super().run(*args)

    async def run():
        service = ContextService(Settings(agent_mode="foundry", foundry_project_endpoint="https://offline.invalid",
                                          foundry_model="offline"), log, Recovers())
        first = await service.get_context(request)
        assert first.mode == "factual" and len(service.cache) == 0
        assert "private" not in first.model_dump_json()
        second = await service.get_context(request)
        assert second.status == "verified" and len(service.cache) == 1
    asyncio.run(run())


def test_cancellation_releases_generation_capacity_and_does_not_cache_partial_output(stored):
    log, request = stored

    async def run():
        entered, release = asyncio.Event(), asyncio.Event()
        class Held(ScriptedRunner):
            async def run(self, *args):
                entered.set()
                await release.wait()
                return await super().run(*args)
        service = ContextService(Settings(app_env="test", agent_mode="scripted", max_concurrent_generations=1),
                                 log, Held())
        task = asyncio.create_task(service.get_context(request))
        await asyncio.wait_for(entered.wait(), 2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert service._active == 0 and len(service.cache) == 0
        release.set()
        assert (await service.get_context(request)).status == "verified"
    asyncio.run(run())


def test_deadline_returns_explicit_factual_output_within_configured_budget(stored):
    log, request = stored
    class Slow(ScriptedRunner):
        async def run(self, *args):
            await asyncio.sleep(1)
    service = ContextService(Settings(app_env="test", agent_mode="scripted", context_timeout_seconds=.1), log, Slow())
    result = asyncio.run(service.get_context(request))
    assert result.mode == "factual" and "deadline" in result.rejection_codes
    assert service._active == 0 and len(service.cache) == 0
