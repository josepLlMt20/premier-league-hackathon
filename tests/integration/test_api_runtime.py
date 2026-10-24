import asyncio
import time
from contextlib import asynccontextmanager

from fastapi.testclient import TestClient
import pytest

from match_context.config import Settings
from match_context.storage.sqlite import SQLiteEventLog


def test_local_runtime_ingests_independently_and_retains_state_after_shutdown(tmp_path, monkeypatch):
    from match_context.server import create_local_app
    original_position = SQLiteEventLog.position
    def off_loop_position(log, match_id):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return original_position(log, match_id)
        raise AssertionError("Synchronous storage I/O on the event loop")
    monkeypatch.setattr(SQLiteEventLog, "position", off_loop_position)
    path = tmp_path / "runtime.sqlite3"
    app = create_local_app(Settings(), database=path, initial_second=10, speed=300)
    with TestClient(app) as client:
        match_id = client.get("/api/matches").json()[0]["match_id"]
        base = f"/api/matches/{match_id}"
        deadline = time.monotonic() + 3
        head = client.get(base + "/head").json()
        while head["available_second"] <= 10 and time.monotonic() < deadline:
            time.sleep(.02)
            head = client.get(base + "/head").json()
        assert head["available_second"] > 10
        old = client.get(base + "/view?to_sequence=0").json()
        assert old["cutoff_sequence"] == 0 and old["recent_events"] == []
        assert client.get(base + "/head").json()["available_second"] >= head["available_second"]
    log = SQLiteEventLog(path)
    try:
        assert log.position(match_id).available_second >= head["available_second"]
    finally:
        log.close()


def test_unavailable_foundry_startup_keeps_data_and_factual_context_available(tmp_path, monkeypatch):
    from match_context.server import create_local_app
    from match_context.agents import foundry
    @asynccontextmanager
    async def unavailable(**kwargs):
        assert kwargs["project_endpoint"] == "https://offline.invalid"
        raise RuntimeError("private provider authentication detail")
        yield
    monkeypatch.setattr(foundry, "local_foundry_runner", unavailable)
    settings = Settings(agent_mode="foundry", foundry_project_endpoint="https://offline.invalid", foundry_model="offline")
    app = create_local_app(settings, database=tmp_path / "no-model.sqlite3", initial_second=10)
    with TestClient(app) as client:
        match_id = client.get("/api/matches").json()[0]["match_id"]
        result = client.post("/api/context", json={"match_id": match_id, "from_sequence": 0, "to_sequence": 0})
        assert result.status_code == 200 and result.json()["mode"] == "factual"
        assert "provider_unavailable" in result.json()["rejection_codes"]
        assert "private" not in result.text
        assert client.get(f"/api/matches/{match_id}/view?to_sequence=0").status_code == 200


def test_local_launcher_requires_explicit_injection_for_scripted_mode(tmp_path):
    from match_context.server import create_local_app
    with pytest.raises(ValueError):
        create_local_app(Settings(agent_mode="scripted"), database=tmp_path / "unused.sqlite3")
