"""Orchestrate the ClaimLens analysis steps."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from .claim_extractor import Claim
from .evidence_analyzer import EvidenceAssessment
from .evidence_collector import Evidence, _keywords_from_text, collect_evidence_for_claim
from .input_reader import AnalysisRequest
from .repository_info import get_commit_sha


@dataclass(frozen=True)
class AnalysisResult:
    request: AnalysisRequest
    claims: List[Claim]
    evidence: List[Evidence]
    assessments: List[EvidenceAssessment]
    repository_commit: str = "unavailable"


class ClaimExtractorProtocol:
    def extract_claims(self, report):
        raise NotImplementedError


class EvidenceAnalyzerProtocol:
    def analyze(self, claim, evidence):
        raise NotImplementedError


def analyze_request(
    request: AnalysisRequest,
    claim_extractor: ClaimExtractorProtocol,
    evidence_analyzer: EvidenceAnalyzerProtocol,
    base_dir: Union[str, Path] = ".",
    extra_evidence: Optional[List[Evidence]] = None,
) -> AnalysisResult:
    """Run the complete analysis flow using injected components."""
    claims = claim_extractor.extract_claims(request.report)
    evidence = []
    assessments = []
    seen_evidence = set()
    extra_evidence = extra_evidence or []
    for claim in claims:
        claim_evidence = collect_evidence_for_claim(request, claim.text, base_dir=base_dir)
        keywords = _keywords_from_text(claim.text)
        claim_evidence.extend(
            item for item in extra_evidence
            if any(keyword in item.text.lower() for keyword in keywords)
        )
        assessments.append(evidence_analyzer.analyze(claim, claim_evidence))
        for item in claim_evidence:
            key = (item.file, item.line)
            if key not in seen_evidence:
                evidence.append(item)
                seen_evidence.add(key)
    return AnalysisResult(
        request=request,
        claims=claims,
        evidence=evidence,
        assessments=assessments,
        repository_commit=get_commit_sha(request.repository_path, base_dir=base_dir),
    )
