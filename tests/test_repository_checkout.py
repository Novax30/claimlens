from claimlens.repository_checkout import ensure_repository_checkout


def test_existing_checkout_is_reused(tmp_path):
    target = tmp_path / "cache" / "owner-repo"
    (target / ".git").mkdir(parents=True)

    result = ensure_repository_checkout("owner/repo", cache_dir=tmp_path / "cache")

    assert result == target
