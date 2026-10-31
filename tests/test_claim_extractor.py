from claimlens.claim_extractor import extract_claims
from claimlens.input_reader import ReportInput


def test_extract_claims_splits_title_and_body():
    report = ReportInput(
        title="Negative timeout values are rejected",
        body="The project raises an error for negative values. The behavior is documented.",
    )

    claims = extract_claims(report)

    assert [claim.text for claim in claims] == [
        "Negative timeout values are rejected",
        "The project raises an error for negative values",
        "The behavior is documented",
    ]
    assert claims[0].claim_type == "configuration"


def test_extract_claims_removes_duplicates():
    report = ReportInput(
        title="Timeout is broken",
        body="Timeout is broken. Timeout is broken!",
    )

    claims = extract_claims(report)

    assert len(claims) == 1


def test_extract_claims_classifies_security_claims():
    report = ReportInput(
        title="Possible vulnerability",
        body="The dependency may be vulnerable.",
    )

    claims = extract_claims(report)

    assert claims[0].claim_type == "security"
