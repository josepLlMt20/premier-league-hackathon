import asyncio
import json
import socket

import httpx
import pytest
from fastapi.testclient import TestClient

from match_context.analysis.snapshot import build_snapshot
from match_context.config import Settings
from match_context.simulation.ingest import Ingestor
from match_context.storage.sqlite import SQLiteEventLog
from tests.unit.agent_helpers import ScriptedRunner


@pytest.fixture
def api_case(tmp_path, scenario_main):
    from match_context.api.app import create_app
    log = SQLiteEventLog(tmp_path / "api.sqlite3")
    ingestor = Ingestor(log, (scenario_main,))
    ingestor.tick(scenario_main.metadata.match_id, 1500)
    runner = ScriptedRunner()
    settings = Settings(app_env="test", agent_mode="scripted")
    app = create_app(settings, log, runner)
    yield app, log, scenario_main, ingestor, runner
    log.close()


def request_for(match, cutoff=269, **changes):
    return {"match_id": match.metadata.match_id, "from_sequence": 0, "to_sequence": cutoff, **changes}


def test_catalog_and_head_reveal_no_future_score_or_fixture(api_case):
    app, log, match, _, _ = api_case
    with TestClient(app) as client:
        catalog = client.get("/api/matches")
        assert catalog.json() == [match.metadata.model_dump(mode="json")]
        head = client.get(f"/api/matches/{match.metadata.match_id}/head")
        assert head.json()["sequence"] == log.head(match.metadata.match_id)
        assert head.json()["available_second"] == 1500
        assert "score" not in head.json()
        assert catalog.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("suffix", ["view?to_sequence=99999", "cursor?available_second=1501"])
def test_future_view_or_cursor_is_rejected(api_case, suffix):
    app, _, match, _, _ = api_case
    with TestClient(app) as client:
        response = client.get(f"/api/matches/{match.metadata.match_id}/{suffix}")
    assert response.status_code == 422
    assert response.json()["error"]["code"] in ("future_cutoff", "future_time")


def test_view_and_cursor_reconstruct_old_prefix_beyond_recent_event_window(api_case):
    app, _, match, _, _ = api_case
    second = match.events[9].available_second
    cutoff = max(e.sequence for e in match.events if e.available_second <= second)
    with TestClient(app) as client:
        cursor = client.get(f"/api/matches/{match.metadata.match_id}/cursor", params={"available_second": second}).json()
        assert cursor["to_sequence"] == cutoff
        old = client.get(f"/api/matches/{match.metadata.match_id}/view", params={"to_sequence": cutoff}).json()
        latest = client.get(f"/api/matches/{match.metadata.match_id}/view", params={"to_sequence": 269}).json()
    assert len(latest["recent_events"]) == 100
    assert all(event["sequence"] <= cutoff for event in old["recent_events"])
    expected = build_snapshot(match.events, cutoff, match.metadata)
    assert old["snapshot_id"] == expected.snapshot_id
    assert old["score"] == [item.model_dump() for item in expected.score]
    assert all(fact["cutoff_sequence"] == cutoff for fact in old["facts"])


def test_context_evidence_and_errors_remain_bounded_and_public(api_case):
    app, _, match, _, runner = api_case
    with TestClient(app) as client:
        result = client.post("/api/context", json=request_for(match)).json()
        assert result["status"] == "verified" and result["mode"] == "scripted"
        calls = len(runner.calls)
        assert client.post("/api/context", json=request_for(match)).json() == result
        assert len(runner.calls) == calls
        empty = client.post("/api/context", json=request_for(match, 0)).json()
        assert empty["status"] == "insufficient" and empty["cards"] == []
        response = client.post("/api/evidence", json={"match_id": match.metadata.match_id,
            "to_sequence": 269, "event_ids": [match.events[269].event_id]})
        assert response.status_code == 422
        response = client.post("/api/evidence", json={"match_id": match.metadata.match_id,
            "to_sequence": 269, "event_ids": [result["evidence_ids"][0]]})
        assert all(e["sequence"] <= 269 for e in response.json()["events"])
        assert client.get("/api/matches/missing/head").status_code == 404
        invalid = client.post("/api/context", json={**request_for(match), "snapshot": "private-config-value"})
        assert invalid.status_code == 422 and "private-config-value" not in invalid.text
    assert not {"fixture", "manifest", "prompt", "configuration"} & result.keys()


def test_context_rejects_future_or_unknown_favorite_without_model_call(api_case):
    app, _, match, _, runner = api_case
    with TestClient(app) as client:
        assert client.post("/api/context", json=request_for(match, 99999)).status_code == 422
        assert client.post("/api/context", json=request_for(match, favorite_team_id="outsider")).status_code == 422
    assert not runner.calls


def test_corrections_and_simultaneous_arrivals_follow_available_clock(tmp_path, scenario_correction):
    from match_context.api.app import create_app
    log = SQLiteEventLog(tmp_path / "correction.sqlite3")
    try:
        ingestor = Ingestor(log, (scenario_correction,))
        correction = next(e for e in scenario_correction.events if e.kind == "correction")
        ingestor.tick(scenario_correction.metadata.match_id, correction.available_second)
        with TestClient(create_app(Settings(), log)) as client:
            base = f"/api/matches/{scenario_correction.metadata.match_id}"
            cursor = client.get(base + "/cursor", params={"available_second": correction.available_second - 1}).json()
            old = client.get(base + "/view", params={"to_sequence": cursor["to_sequence"]}).json()
            new = client.get(base + "/view", params={"to_sequence": correction.sequence}).json()
            assert correction.attributes.target_event_id not in old["annulled_event_ids"]
            assert correction.attributes.target_event_id in new["annulled_event_ids"]
            same = client.get(base + "/cursor", params={"available_second": correction.available_second}).json()
            assert same["to_sequence"] == max(e.sequence for e in scenario_correction.events
                                              if e.available_second <= correction.available_second)
    finally:
        log.close()


def test_later_response_finishes_first_without_contaminating_earlier_request(api_case):
    from match_context.api.app import create_app
    _, log, match, _, _ = api_case

    async def run():
        entered, release = asyncio.Event(), asyncio.Event()

        class Delayed(ScriptedRunner):
            async def run(self, role, payload, tools):
                if role == "analyst" and payload["request"]["to_sequence"] == 268:
                    entered.set()
                    await release.wait()
                return await super().run(role, payload, tools)

        app = create_app(Settings(app_env="test", agent_mode="scripted"), log, Delayed())
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            early_task = asyncio.create_task(client.post("/api/context", json=request_for(match, 268)))
            await asyncio.wait_for(entered.wait(), 2)
            late = await client.post("/api/context", json=request_for(match, 269))
            assert late.status_code == 200 and not early_task.done()
            release.set()
            early = await early_task
        assert early.json()["request"]["to_sequence"] == 268
        assert late.json()["request"]["to_sequence"] == 269
        assert early.json()["snapshot_id"] != late.json()["snapshot_id"]
        assert all(f["cutoff_sequence"] == 268 for f in early.json()["facts"])
    asyncio.run(run())


def test_two_generations_limit_does_not_block_views_and_slots_recover(api_case):
    from match_context.api.app import create_app
    _, log, match, _, _ = api_case

    async def run():
        ready, release = asyncio.Event(), asyncio.Event()

        class Held(ScriptedRunner):
            entered = 0
            async def run(self, role, payload, tools):
                if role == "analyst":
                    self.entered += 1
                    if self.entered == 2:
                        ready.set()
                    await release.wait()
                return await super().run(role, payload, tools)

        app = create_app(Settings(app_env="test", agent_mode="scripted"), log, Held())
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            tasks = [asyncio.create_task(client.post("/api/context", json=request_for(match, cutoff)))
                     for cutoff in (268, 269)]
            await asyncio.wait_for(ready.wait(), 2)
            busy = await client.post("/api/context", json=request_for(match, 267))
            assert busy.status_code == 429 and busy.headers["retry-after"] == "1"
            assert (await client.get(f"/api/matches/{match.metadata.match_id}/view?to_sequence=10")).status_code == 200
            release.set()
            assert all(r.status_code == 200 for r in await asyncio.gather(*tasks))
            assert (await client.post("/api/context", json=request_for(match, 267))).status_code == 200
    asyncio.run(run())


def test_storage_error_is_sanitized_and_health_stays_independent(api_case, monkeypatch):
    app, log, match, _, _ = api_case
    monkeypatch.setattr(log, "position", lambda match_id: (_ for _ in ()).throw(RuntimeError("private endpoint and token")))
    with TestClient(app) as client:
        assert client.get("/healthz").status_code == 200
        response = client.get(f"/api/matches/{match.metadata.match_id}/head")
        assert response.status_code == 503 and "private" not in response.text


def test_http_disconnect_cancels_generation_and_allows_replacement_request(api_case):
    from match_context.api.app import create_app
    _, log, match, _, _ = api_case

    async def run():
        entered, cancelled = asyncio.Event(), asyncio.Event()

        class Abandoned(ScriptedRunner):
            first = True
            async def run(self, role, payload, tools):
                if role == "analyst" and self.first:
                    self.first = False
                    entered.set()
                    try:
                        await asyncio.Event().wait()
                    except asyncio.CancelledError:
                        cancelled.set()
                        raise
                return await super().run(role, payload, tools)

        app = create_app(Settings(app_env="test", agent_mode="scripted", max_concurrent_generations=1),
                         log, Abandoned())
        messages, sent = asyncio.Queue(), []
        body = json.dumps(request_for(match)).encode()
        await messages.put({"type": "http.request", "body": body, "more_body": False})
        async def receive():
            return await messages.get()
        async def send(message):
            sent.append(message)
        scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "POST",
                 "scheme": "http", "path": "/api/context", "raw_path": b"/api/context", "root_path": "",
                 "query_string": b"", "headers": [(b"content-type", b"application/json")],
                 "client": ("127.0.0.1", 1111), "server": ("test", 80)}
        task = asyncio.create_task(app(scope, receive, send))
        try:
            await asyncio.wait_for(entered.wait(), 2)
            assert app.state.context_service._active == 1
            await messages.put({"type": "http.disconnect"})
            await asyncio.wait_for(cancelled.wait(), .5)
            await asyncio.wait_for(task, 1)
            assert app.state.context_service._active == 0
            assert len(app.state.context_service.cache) == 0
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                replacement = await client.post("/api/context", json=request_for(match))
            assert replacement.status_code == 200 and replacement.json()["status"] == "verified"
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    asyncio.run(run())


def test_real_tcp_disconnect_releases_generation_slot(api_case):
    import uvicorn
    from match_context.api.app import create_app
    _, log, match, _, _ = api_case

    async def run():
        entered, cancelled = asyncio.Event(), asyncio.Event()
        class Held(ScriptedRunner):
            first = True
            async def run(self, role, payload, tools):
                if role == "analyst" and self.first:
                    self.first = False
                    entered.set()
                    try:
                        await asyncio.Event().wait()
                    except asyncio.CancelledError:
                        cancelled.set()
                        raise
                return await super().run(role, payload, tools)

        app = create_app(Settings(app_env="test", agent_mode="scripted", max_concurrent_generations=1), log, Held())
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, log_level="critical", lifespan="off", timeout_graceful_shutdown=1))
        server_task = asyncio.create_task(server.serve(sockets=[sock]))
        writer = None
        try:
            async def started():
                while not server.started:
                    await asyncio.sleep(.005)
            await asyncio.wait_for(started(), 2)
            _, writer = await asyncio.open_connection("127.0.0.1", port)
            body = json.dumps(request_for(match)).encode()
            writer.write(b"POST /api/context HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\n"
                         + f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
            await writer.drain()
            await asyncio.wait_for(entered.wait(), 2)
            writer.close()
            await writer.wait_closed()
            await asyncio.wait_for(cancelled.wait(), 1)
            async def released():
                while app.state.context_service._active:
                    await asyncio.sleep(.001)
            await asyncio.wait_for(released(), 1)
            assert len(app.state.context_service.cache) == 0
            async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}") as client:
                response = await client.post("/api/context", json=request_for(match))
            assert response.status_code == 200 and response.json()["status"] == "verified"
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
            server.should_exit = True
            await asyncio.wait_for(server_task, 3)
            sock.close()
    asyncio.run(run())
