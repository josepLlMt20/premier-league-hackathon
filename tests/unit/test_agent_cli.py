import json
import pytest

from match_context.agent_cli import main


def test_default_cli_is_explicit_factual_output_without_model_calls(capsys):
    assert main(["--until-second", "1500", "--language", "en", "--role", "commentator"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "factual"
    assert report["mode"] == "factual"
    assert "Factual summary" in report["summary"]
    assert report["trace"]["model_calls"] == 0
    assert report["request"]["role"] == "commentator"


@pytest.mark.parametrize("args", [["--until-second", "5401"],
                                   ["--from-second", "1500", "--until-second", "1200"]])
def test_cli_rejects_invalid_time_intervals(args):
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == 2
