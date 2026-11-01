import os

from claimlens.github_pr_verifier import _run_git


def test_git_checkout_auth_uses_temporary_askpass_not_url(monkeypatch, tmp_path):
    captured = {}

    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command, env, capture_output, text, timeout):
        captured["command"] = command
        captured["env"] = env
        return Completed()

    monkeypatch.setattr("claimlens.github_pr_verifier.subprocess.run", fake_run)
    _run_git(["clone", "https://github.com/o/r.git", str(tmp_path / "repo")], "secret-token", 10)

    assert "secret-token" not in captured["command"]
    assert captured["env"]["CLAIMLENS_GIT_TOKEN"] == "secret-token"
    assert "GIT_ASKPASS" in captured["env"]
    assert captured["env"].get("GITHUB_TOKEN") is None
    assert not os.path.exists(captured["env"]["GIT_ASKPASS"])
