"""Local, single-process API with one independent durable ingestion scheduler."""

import argparse
import asyncio
from contextlib import AsyncExitStack, asynccontextmanager
import logging
from pathlib import Path
import time

from match_context.api.app import create_app
from match_context.config import Settings
from match_context.simulation.fixtures import scenario_manifest
from match_context.simulation.generator import generate_match
from match_context.simulation.ingest import Ingestor
from match_context.storage.sqlite import SQLiteEventLog


def create_local_app(settings=None, *, database="tmp/matches.sqlite3", scenario="main", seed=None,
                     speed=30, initial_second=0):
    settings = settings or Settings.from_env()
    if settings.storage_backend != "sqlite" or settings.agent_mode == "scripted":
        raise ValueError("Local launcher requires SQLite and factual/Foundry mode; use create_app for injected adapters")
    if type(initial_second) is not int or not 0 <= initial_second <= 5400:
        raise ValueError("Initial ingestion second is out of range")
    Ingestor._check_elapsed(speed, positive=True)
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    log = SQLiteEventLog(path)
    try:
        source = generate_match(scenario, scenario_manifest(scenario).seed if seed is None else seed)
        ingestor = Ingestor(log, (source,), speed=speed)
        match_id = source.metadata.match_id
        ingestor.tick(match_id, max(initial_second, log.position(match_id).available_second))
    except BaseException:
        log.close()
        raise

    @asynccontextmanager
    async def lifespan(app):
        stop = asyncio.Event()
        task = None
        async with AsyncExitStack() as resources:
            try:
                if settings.agent_mode == "foundry":
                    try:
                        from match_context.agents.foundry import local_foundry_runner
                        app.state.context_service.runner = await resources.enter_async_context(local_foundry_runner(
                            project_endpoint=settings.foundry_project_endpoint, model=settings.foundry_model))
                    except Exception:
                        logging.getLogger(__name__).warning("Foundry startup unavailable; factual context remains available")
                app.state.ingestion_states[match_id] = (await asyncio.to_thread(ingestor.status, match_id)).state

                def advance(elapsed):
                    ingestor.advance(match_id, elapsed)
                    return ingestor.status(match_id).state

                async def ingest():
                    previous = time.monotonic()
                    while not stop.is_set() and app.state.ingestion_states[match_id] == "running":
                        try:
                            await asyncio.wait_for(stop.wait(), timeout=.05)
                            break
                        except TimeoutError:
                            pass
                        now = time.monotonic()
                        try:
                            app.state.ingestion_states[match_id] = await asyncio.to_thread(advance, now - previous)
                        except Exception:
                            app.state.ingestion_states[match_id] = "failed"
                            logging.getLogger(__name__).warning("Shared ingestion stopped at its last durable position")
                        previous = now

                task = asyncio.create_task(ingest())
                yield
            finally:
                stop.set()
                if task is not None:
                    # Do not close storage under a still-running worker thread.
                    await task
                await asyncio.to_thread(log.close)
    return create_app(settings, log, lifespan=lifespan)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="tmp/matches.sqlite3")
    parser.add_argument("--scenario", choices=("main", "neutral", "sterile", "correction"), default="main")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--speed", type=float, default=30)
    parser.add_argument("--initial-second", type=int, default=0)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between one and 65535")
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
    import uvicorn
    app = create_local_app(Settings.from_env(), database=args.database, scenario=args.scenario, seed=args.seed,
                           speed=args.speed, initial_second=args.initial_second)
    uvicorn.run(app, host=args.host, port=args.port, workers=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
