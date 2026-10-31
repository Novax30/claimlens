from claimlens.input_reader import ReportInput
from claimlens.quality_checker import assess_report_quality


def test_quality_checker_finds_missing_details():
    quality = assess_report_quality(ReportInput("Timeout bug", "The timeout is broken."))

    assert quality.status == "incomplete"
    assert "reproduction steps or an example" in quality.missing


def test_quality_checker_accepts_detailed_report():
    quality = assess_report_quality(
        ReportInput(
            "Timeout bug",
            "Expected: timeout rejects zero. Actual: it crashes. "
            "Reproduction steps: run python app.py. Python 3.11.",
        )
    )

    assert quality.status == "complete"
    assert quality.missing == []
