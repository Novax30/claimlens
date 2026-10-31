from claimlens.input_reader import load_request
from claimlens.service import ClaimLensService
from claimlens.input_reader import AnalysisRequest, ReportInput
from pathlib import Path


def test_offline_service_analyzes_without_ollama():
    service = ClaimLensService(offline=True)

    result = service.analyze_file("input/example_request.json")

    assert result.assessments
    assert result.assessments[0].assessment == "contradicted"
    assert result.assessments[0].confidence == "high"
    assert result.assessments[0].execution_status == "not_attempted"


def test_offline_service_generates_report():
    service = ClaimLensService(offline=True)
    result = service.analyze_file("input/example_request.json")

    report = service.to_markdown(result)

    assert "ClaimLens Assessment" in report
    assert "contradicted" in report


def test_offline_service_checks_numeric_default_against_repository():
    service = ClaimLensService(offline=True)
    supported = service.analyze_request(
        AnalysisRequest(
            Path("examples/sample_project"),
            ReportInput("The default timeout is 30 seconds", "The default timeout is 30 seconds."),
        )
    )
    contradicted = service.analyze_request(
        AnalysisRequest(
            Path("examples/sample_project"),
            ReportInput("The default timeout is 60 seconds", "The default timeout is 60 seconds."),
        )
    )

    assert supported.assessments[0].assessment == "supported"
    assert contradicted.assessments[0].assessment == "contradicted"
