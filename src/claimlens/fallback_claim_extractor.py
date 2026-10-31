"""Model-free claim extraction fallback."""

from typing import List

from .claim_extractor import Claim, extract_claims
from .input_reader import ReportInput


class FallbackClaimExtractor:
    def extract_claims(self, report: ReportInput) -> List[Claim]:
        return extract_claims(report)
