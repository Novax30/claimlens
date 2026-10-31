from claimlens.verification_runner import run_repository_tests


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
