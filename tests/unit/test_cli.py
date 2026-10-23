import json

import pytest

from match_context.cli import main


def test_cli_outputs_factual_context_and_evidence_at_the_requested_point(capsys):
    assert main(["--scenario", "main", "--until-second", "1500", "--include-evidence"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["score"] == {"amber": 1, "cobalt": 0}
    assert report["clock_second"] == 1500
    assert any(story["pattern"] == "high_recoveries" and story["delta"] == 3 for story in report["stories"])
    assert all(event["sequence"] <= report["cutoff_sequence"] for event in report["evidence"]["events"])
    assert all(event["available_second"] <= 1500 for event in report["evidence"]["events"])


def test_cli_correction_preserves_the_earlier_score(capsys):
    main(["--scenario", "correction", "--until-second", "1500"])
    assert json.loads(capsys.readouterr().out)["score"] == {"amber": 1, "cobalt": 0}
    main(["--scenario", "correction", "--until-second", "1600"])
    assert json.loads(capsys.readouterr().out)["score"] == {"amber": 0, "cobalt": 0}


def test_cli_empty_neutral_context_is_honest(capsys):
    main(["--scenario", "neutral", "--until-second", "0"])
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "insufficient"
    assert report["stories"] == []
    assert "evidence" not in report


@pytest.mark.parametrize("arguments", [["--until-second", "5401"], ["--from-second", "1600", "--until-second", "1500"]])
def test_cli_rejects_invalid_clock_intervals(arguments):
    with pytest.raises(SystemExit) as error:
        main(arguments)
    assert error.value.code == 2
