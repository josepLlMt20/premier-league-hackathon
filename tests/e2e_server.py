"""Loopback-only real HTTP/SQLite backend with explicit scripted agents for UI tests.

Never imported by the production launcher. No credentials or model calls.
"""
import argparse
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from match_context.agents.base import AgentOutput
from match_context.api.app import create_app
from match_context.config import Settings
from match_context.simulation.generator import generate_match
from match_context.simulation.ingest import Ingestor
from match_context.storage.sqlite import SQLiteEventLog
from tests.unit.agent_helpers import ScriptedRunner, draft_for


class BilingualScriptedRunner(ScriptedRunner):
    async def run(self, role, payload, tools):
        if role != "writer":
            return await super().run(role, payload, tools)
        cards = []
        for story in payload["stories"]:
            draft = draft_for(story)
            if payload["request"]["language"] == "en":
                draft = draft.model_copy(update={field: getattr(draft, field).model_copy(update={
                    "text": getattr(draft, field).text.replace("recuperaciones altas:", "high recoveries:")
                        .replace("antes", "previously")
                }) for field in ("headline", "explanation", "suggested_line", "overlay")})
            cards.append(draft)
        return AgentOutput(cards=tuple(cards))


def make_app():
    directory = TemporaryDirectory(prefix="match-context-e2e-")
    log = SQLiteEventLog(Path(directory.name) / "events.sqlite3")
    source = generate_match("main", 7)
    ingestor = Ingestor(log, (source,), speed=1)
    match_id = source.metadata.match_id
    ingestor.tick(match_id, 1500)

    @asynccontextmanager
    async def lifespan(app):
        async def ingest():
            while True:
                await asyncio.sleep(1)
                await asyncio.to_thread(ingestor.advance, match_id, 1)
        task = asyncio.create_task(ingest())
        app.state.ingestion_states[match_id] = "running"
        try:
            yield
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            log.close()
            directory.cleanup()

    return create_app(Settings(app_env="test", agent_mode="scripted"), log, BilingualScriptedRunner(), lifespan=lifespan)


if __name__ == "__main__":
    import uvicorn
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    uvicorn.run(make_app(), host="127.0.0.1", port=parser.parse_args().port, workers=1)
