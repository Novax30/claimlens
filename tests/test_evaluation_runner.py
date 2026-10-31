from claimlens.evaluation_runner import evaluate_dataset
from claimlens.service import ClaimLensService


def test_evaluation_dataset_returns_transparent_metrics():
    summary = evaluate_dataset(
        "examples/evaluation_dataset.json",
        ClaimLensService(offline=True),
    )

    assert summary["cases"] == 6
    assert 0 <= summary["accuracy"] <= 1
    assert 0 <= summary["evidence_coverage"] <= 1
    assert len(summary["results"]) == 6
