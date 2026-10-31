"""Stable application service for future CLI, chatbot, editor, and GitHub adapters."""

from pathlib import Path
from typing import List, Optional, Sequence, Union

from .evidence_analyzer import EvidenceAnalyzer
from .evidence_collector import Evidence
from .input_reader import AnalysisRequest, load_request
from .model_claim_extractor import ModelClaimExtractor
from .ollama_client import OllamaClient
from .fallback_claim_extractor import FallbackClaimExtractor
from .offline_analyzer import OfflineEvidenceAnalyzer
from .pipeline import AnalysisResult, analyze_request
from .report_generator import render_markdown_report


class ClaimLensService:
    """Expose ClaimLens analysis without tying it to a user interface."""

    def __init__(
        self,
        claim_model: str = "qwen2.5:7b",
        evidence_model: str = "deepseek-coder:6.7b",
        offline: bool = False,
    ) -> None:
        if offline:
            self.claim_extractor = FallbackClaimExtractor()
            self.evidence_analyzer = OfflineEvidenceAnalyzer()
        else:
            self.claim_extractor = ModelClaimExtractor(OllamaClient(claim_model))
            self.evidence_analyzer = EvidenceAnalyzer(OllamaClient(evidence_model))

    def analyze_request(
        self,
        request: AnalysisRequest,
        base_dir: Union[str, Path] = ".",
        extra_evidence: Optional[List[Evidence]] = None,
    ) -> AnalysisResult:
        return analyze_request(
            request,
            self.claim_extractor,
            self.evidence_analyzer,
            base_dir=base_dir,
            extra_evidence=extra_evidence,
        )

    def analyze_file(
        self,
        request_path: Union[str, Path],
        base_dir: Union[str, Path] = ".",
    ) -> AnalysisResult:
        return self.analyze_request(load_request(request_path), base_dir=base_dir)

    @staticmethod
    def to_markdown(result: AnalysisResult) -> str:
        return render_markdown_report(
            result.request.report,
            result.assessments,
            result.evidence,
            repository_commit=result.repository_commit,
        )
