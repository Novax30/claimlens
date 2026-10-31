from claimlens.pr_queue import analyze_pr_queue, render_queue_markdown
from claimlens.service import ClaimLensService


def test_pr_queue_processes_and_ranks_saved_prs():
    items = analyze_pr_queue(
        "examples/pr_payloads",
        "examples/sample_project",
        ClaimLensService(offline=True),
    )

    assert len(items) == 3
    assert items[0].priority in {"high", "medium", "low"}
    assert {item.number for item in items} == {"101", "102", "103"}


def test_pr_queue_report_is_readable():
    items = analyze_pr_queue(
        "examples/pr_payloads",
        "examples/sample_project",
        ClaimLensService(offline=True),
    )

    report = render_queue_markdown(items)

    assert "# ClaimLens PR Review Queue" in report
    assert "#101" in report
    assert "maintainer must review" in report
    assert "Missing details" in report
