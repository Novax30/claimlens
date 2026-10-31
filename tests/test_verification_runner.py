from claimlens.verification_runner import _docker_command, run_repository_tests


def test_verification_runner_passes_sample_project():
    result = run_repository_tests("examples/sample_project", timeout_seconds=30)

    assert result.status == "passed"
    assert result.exit_code == 0


def test_verification_runner_reports_failure(tmp_path):
    (tmp_path / "test_failure.py").write_text("def test_failure():\n    assert False\n", encoding="utf-8")

    result = run_repository_tests(
        str(tmp_path),
        command=("python", "-m", "pytest", "-q"),
        timeout_seconds=30,
    )

    assert result.status == "failed"
    assert result.exit_code != 0


def test_language_profiles_detect_common_repository_markers(tmp_path):
    from claimlens.language_profiles import detect_language

    (tmp_path / "Cargo.toml").write_text("[package]\nname='demo'\n", encoding="utf-8")
    assert detect_language(tmp_path).name == "Rust"


def test_unknown_language_reports_environment_failure(tmp_path):
    result = run_repository_tests(tmp_path)

    assert result.status == "environment_failure"
    assert result.language == "unknown"


def test_docker_command_has_safety_controls(tmp_path):
    command = _docker_command(tmp_path, ("python", "-m", "pytest"), "python:3.11-slim")

    assert "--network" in command and "none" in command
    assert "--read-only" in command
    assert "--cap-drop" in command and "ALL" in command
    assert "--user" in command and "65532:65532" in command
