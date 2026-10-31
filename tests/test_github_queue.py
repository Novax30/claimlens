from claimlens.github_api import GitHubClient
from claimlens.github_queue import _diff_evidence, analyze_github_prs
from claimlens.service import ClaimLensService


def test_diff_evidence_keeps_new_file_line_numbers():
    evidence = _diff_evidence([
        {
            "filename": "src/config.py",
            "patch": "@@ -7,0 +8,2 @@\n+timeout = 1\n+raise ValueError()",
        }
    ])

    assert evidence[0].file == "PR diff/src/config.py"
    assert evidence[0].line == 8
    assert evidence[1].line == 9


def test_live_queue_uses_pr_files_without_writing_to_github():
    class FakeClient(GitHubClient):
        def list_pull_requests(self, repository, state="open"):
            return [{"number": 7, "title": "Fix timeout", "body": "Reject timeout values."}]

        def list_pull_request_files(self, repository, number):
            return [{
                "filename": "src/config.py",
                "patch": "@@ -1 +1 @@\n+raise ValueError('timeout')",
            }]

    items = analyze_github_prs(
        "o/r", "examples/sample_project", ClaimLensService(offline=True), FakeClient()
    )

    assert len(items) == 1
    assert items[0].number == "7"
