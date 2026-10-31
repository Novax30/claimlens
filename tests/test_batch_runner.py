from claimlens.batch_runner import run_batch
from claimlens.service import ClaimLensService


def test_offline_batch_processes_all_cases():
    results = run_batch("examples/cases", ClaimLensService(offline=True))

    assert len(results) == 12
    assert {result.case_id for result in results}.__len__() == 12
    assessed = [result for result in results if result.analysis.assessments]
    assert len(assessed) == 11
    assert results[-1].case_id == "12_malformed_report"
