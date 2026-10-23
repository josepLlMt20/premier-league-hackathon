import json

import pytest

from match_context.ingest_cli import main
from match_context import ingest_cli
from match_context.domain.events import GeneratedMatch
from match_context.storage.sqlite import SQLiteEventLog


def test_cli_restart_continues_and_can_inspect_an_earlier_view(tmp_path, capsys):
    path = str(tmp_path / "match.sqlite3")
    args = ["--database", path, "--scenario", "correction"]
    assert main([*args, "--until-second", "1500"]) == 0
    before = json.loads(capsys.readouterr().out)
    assert before["view"]["score"] == {"amber": 1, "cobalt": 0}
    assert before["ingestion"]["available_second"] == 1500
    assert main([*args, "--until-second", "1600"]) == 0
    after = json.loads(capsys.readouterr().out)
    assert after["view"]["score"] == {"amber": 0, "cobalt": 0}
    assert after["ingestion"]["new_events"] == after["ingestion"]["sequence"] - before["ingestion"]["sequence"]
    assert main([*args, "--until-second", "1600", "--view-second", "1500"]) == 0
    previous = json.loads(capsys.readouterr().out)
    assert previous["view"]["score"] == {"amber": 1, "cobalt": 0}
    assert previous["ingestion"]["new_events"] == 0
    assert previous["view"]["cutoff_sequence"] < previous["ingestion"]["sequence"]


@pytest.mark.parametrize("extra", [
    ["--until-second", "-1"], ["--until-second", "5401"],
    ["--until-second", "0", "--view-second", "1"], ["--speed", "nan"],
])
def test_cli_rejects_invalid_times_and_rates(tmp_path, extra):
    with pytest.raises(SystemExit) as error:
        main(["--database", str(tmp_path / "invalid.sqlite3"), *extra])
    assert error.value.code == 2
    assert not (tmp_path / "invalid.sqlite3").exists()


def test_realtime_command_advances_from_elapsed_time(tmp_path, capsys, monkeypatch):
    moments = iter((0, 1, 2))
    monkeypatch.setattr(ingest_cli.time, "monotonic", lambda: next(moments))
    monkeypatch.setattr(ingest_cli.time, "sleep", lambda _: None)
    assert main(["--database", str(tmp_path / "live.sqlite3"), "--until-second", "60", "--realtime"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ingestion"]["available_second"] == 60
    assert report["ingestion"]["new_events"] > 0
    assert report["view"]["last_event_second"] <= 60


@pytest.mark.parametrize("second", [10, 5400])
def test_realtime_restart_drains_remaining_events_at_its_current_target(tmp_path, capsys, monkeypatch,
                                                                       metadata, make_event, second):
    path = tmp_path / "partial.sqlite3"
    events = tuple(make_event(sequence=i, occurred_second=second, available_second=second,
                              period=1 if second < 2700 else 2) for i in (1, 2))
    match = GeneratedMatch(metadata=metadata, events=events)
    log = SQLiteEventLog(path)
    log.register_match(metadata)
    log.append(events[0])
    log.close()
    monkeypatch.setattr(ingest_cli, "generate_match", lambda *_: match)
    assert main(["--database", str(path), "--until-second", str(second), "--realtime"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ingestion"]["sequence"] == 2
    assert result["ingestion"]["new_events"] == 1
    assert result["view"]["cutoff_sequence"] == 2
