import json
import time

import json

import pytest

from claimlens.github_api import GitHubAPIError, GitHubClient, parse_repository


def test_parse_repository_requires_owner_and_name():
    assert parse_repository("octo/project").owner == "octo"
    with pytest.raises(GitHubAPIError):
        parse_repository("project")


def test_list_pull_requests_reads_json_and_authorization(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps([{"number": 7, "title": "Fix"}]).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        return Response()

    monkeypatch.setattr("claimlens.github_api.urlopen", fake_urlopen)
    result = GitHubClient(token="secret", api_url="https://example.test", cache_dir=None).list_pull_requests("o/r")

    assert result[0]["number"] == 7
    assert captured["url"].startswith("https://example.test/repos/o/r/pulls")
    assert captured["auth"] == "Bearer secret"


def test_list_pull_request_files_uses_files_endpoint(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'[{"filename":"src/config.py","patch":"@@ -1 +1 @@\\n+timeout = 1"}]'

    seen = []

    def fake_urlopen(request, timeout):
        seen.append(request.full_url)
        return Response()

    monkeypatch.setattr("claimlens.github_api.urlopen", fake_urlopen)
    files = GitHubClient(api_url="https://example.test", cache_dir=None).list_pull_request_files("o/r", 7)

    assert files[0]["filename"] == "src/config.py"
    assert "/pulls/7/files" in seen[0]


def test_github_client_uses_fresh_cache(tmp_path, monkeypatch):
    calls = []

    class Response:
        headers = {"X-RateLimit-Remaining": "10"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'[]'

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        return Response()

    monkeypatch.setattr("claimlens.github_api.urlopen", fake_urlopen)
    client = GitHubClient(api_url="https://example.test", cache_dir=str(tmp_path))
    client.list_pull_requests("o/r")
    client.list_pull_requests("o/r")

    assert len(calls) == 1


def test_github_client_stops_after_rate_limit(monkeypatch):
    client = GitHubClient(cache_dir=None)
    client.rate_limit_remaining = 0
    client.rate_limit_reset = int(time.time()) + 60

    with pytest.raises(GitHubAPIError, match="rate limit"):
        client.list_pull_requests("o/r")
