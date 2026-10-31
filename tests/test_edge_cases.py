import json

import pytest

from claimlens.api_adapter import request_from_api_payload
from claimlens.claim_extractor import extract_claims
from claimlens.github_api import GitHubAPIError, parse_repository
from claimlens.github_adapter import request_from_github_payload
from claimlens.input_reader import InputValidationError, ReportInput
from claimlens.language_profiles import detect_language
from claimlens.pr_queue import PRQueueItem, render_queue_markdown
from claimlens.quality_checker import assess_report_quality


INVALID_API_PAYLOADS = [
    None,
    {},
    {"repository_path": ""},
    {"repository_path": 1},
    {"repository_path": "repo"},
    {"repository_path": "repo", "report": None},
    {"repository_path": "repo", "report": []},
    {"repository_path": "repo", "report": {"title": "T"}},
    {"repository_path": "repo", "report": {"body": "B"}},
    {"repository_path": "repo", "report": {"title": "", "body": "B"}},
    {"repository_path": "repo", "report": {"title": "T", "body": ""}},
    {"repository_path": "repo", "report": {"title": 1, "body": "B"}},
    {"repository_path": "repo", "report": {"title": "T", "body": 1}},
    {"repository_path": "repo", "report": {"title": "T", "body": "B", "kind": "comment"}},
    {"repository_path": "repo", "report": {"title": "T", "body": "B", "kind": None}},
    {"repository_path": "repo", "report": {"title": " T ", "body": " B ", "kind": []}},
    {"repository_path": "repo", "report": {"title": "\n", "body": "B"}},
    {"repository_path": "repo", "report": {"title": "T", "body": "\t"}},
    {"repository_path": "repo", "report": {"title": "T", "body": "B", "kind": 3}},
    {"repository_path": "repo", "report": {"title": "T", "body": "B", "kind": "ISSUE"}},
]


@pytest.mark.parametrize("payload", INVALID_API_PAYLOADS)
def test_api_payload_edge_cases_are_rejected(payload):
    with pytest.raises(InputValidationError):
        request_from_api_payload(payload)


CLAIM_TEXTS = [
    "The timeout is 30 seconds.",
    "The timeout is 30 seconds!",
    "The timeout is 30 seconds?",
    "Negative values are rejected.",
    "Negative values are rejected. Negative values are rejected.",
    "A\nB\nC.",
    "Unicode café values are accepted.",
    "Use `timeout=10` in configuration.",
    "First. Second. Third.",
    "First... Second?! Third.",
    "README documentation is incorrect.",
    "Security vulnerability may exist.",
    "The API returns JSON.",
    "The function accepts None.",
    "The function rejects False.",
    "The default configuration is stable.",
    "A/B paths are handled.",
    "A hyphenated-name is valid.",
    "123 values are supported.",
    "Quotes: 'value' and \"value\".",
    "Line one.\nLine two.",
    "Trailing spaces are ignored.   ",
    "Question without punctuation",
    "!!!",
    "",
]


@pytest.mark.parametrize("body", CLAIM_TEXTS)
def test_claim_extraction_edge_cases_is_deterministic(body):
    report = ReportInput("Edge case", body)
    first = extract_claims(report)
    second = extract_claims(report)
    assert first == second
    assert len({claim.text.casefold() for claim in first}) == len(first)


INVALID_REPOSITORIES = [
    "", "/", "repo", "owner/", "/repo", "a/b/c", "a//b", "a\\b",
    "a b/c", "a/c d", "https://github.com/a/b", "a/.", "./a/b",
    "a/b/", "a/b/c/d",
]


@pytest.mark.parametrize("repository", INVALID_REPOSITORIES)
def test_repository_parser_rejects_unsafe_shapes(repository):
    with pytest.raises(GitHubAPIError):
        parse_repository(repository)


QUALITY_CASES = [
    ("nothing", "", 3),
    ("reproducible", "reproduction steps command version expected actual", 0),
    ("steps", "steps", 2),
    ("expected", "expected", 2),
    ("actual", "actual", 2),
    ("version", "version", 2),
    ("example", "example", 2),
    ("command", "command", 2),
    ("OS", "operating system", 2),
    ("dependency", "dependency", 2),
    ("all words", "reproduction expected actual Python 3.11", 0),
    ("should instead", "should instead version", 1),
    ("mixed", "steps should version", 0),
    ("mixed 2", "example actual OS", 1),
    ("mixed 3", "command expected dependency", 0),
    ("empty title", "", 3),
    ("version prefix", "Python version", 2),
    ("repro", "reproduce", 2),
    ("expected only", "expected", 2),
    ("actual only", "actual", 2),
]


@pytest.mark.parametrize("title,body,missing_count", QUALITY_CASES)
def test_quality_checker_reports_expected_missing_fields(title, body, missing_count):
    assert len(assess_report_quality(ReportInput(title, body)).missing) == missing_count


def test_github_payload_accepts_missing_description_as_empty_notice():
    request = request_from_github_payload(
        {"pull_request": {"title": "No body", "body": None}}, "repo"
    )
    assert "No description" in request.report.body


@pytest.mark.parametrize("title", ["a|b", "line\none", "<script>", "100%", "# heading"])
def test_queue_markdown_keeps_special_titles_safe(title):
    item = PRQueueItem("1", title, "low", "lower_priority", "supported", "high", [])
    rendered = render_queue_markdown([item])
    row = rendered.split("| #1 |", 1)[1].split("\n", 1)[0]
    assert "\n" not in row
    if "|" in title:
        assert "\\|" in row


@pytest.mark.parametrize("filename", ["Cargo.toml", "CMakeLists.txt", "package.json", "go.mod", "pyproject.toml"])
def test_language_detection_handles_manifest_names(tmp_path, filename):
    (tmp_path / filename).write_text("", encoding="utf-8")
    assert detect_language(tmp_path) is not None
