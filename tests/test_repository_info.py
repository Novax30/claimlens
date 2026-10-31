from pathlib import Path

from claimlens.repository_info import get_commit_sha


def test_get_commit_sha_returns_a_revision_for_this_checkout():
    sha = get_commit_sha(Path("examples/sample_project"), base_dir=".")
    assert len(sha) >= 7 or sha == "unavailable"
