import json

from claimlens.github_cli import main


def test_github_cli_runs_offline(tmp_path, capsys):
    payload = tmp_path / "payload.json"
    payload.write_text(
        json.dumps(
            {"issue": {"title": "Timeout bug", "body": "Negative values are accepted."}}
        ),
        encoding="utf-8",
    )
    output = tmp_path / "report.md"

    result = main(
        [str(payload), "examples/sample_project", "--offline", "--output", str(output)]
    )

    assert result == 0
    assert output.exists()
    assert "ClaimLens Assessment" in output.read_text(encoding="utf-8")
    assert "report written" in capsys.readouterr().out
