"""Conservative evidence assessment without a language model."""

from typing import List

from .claim_extractor import Claim
from .evidence_analyzer import EvidenceAssessment
from .evidence_collector import Evidence


class OfflineEvidenceAnalyzer:
    def analyze(self, claim: Claim, evidence: List[Evidence]) -> EvidenceAssessment:
        if not evidence:
            return EvidenceAssessment(
                claim=claim.text,
                assessment="uncertain",
                confidence="low",
                explanation="No relevant evidence was found by the offline analyzer.",
                evidence_refs=[],
            )

        rejection_markers = (
            "raise valueerror",
            "raise typeerror",
            "rejected",
            "must be greater than zero",
        )
        rejection_evidence = [
            item for item in evidence if any(marker in item.text.lower() for marker in rejection_markers)
        ]
        refs = [f"{item.file}:{item.line}" for item in rejection_evidence]
        lowered_claim = claim.text.lower()

        if rejection_evidence and any(
            word in lowered_claim for word in ("accepts", "accepted", "allows", "allow")
        ):
            return EvidenceAssessment(
                claim=claim.text,
                assessment="contradicted",
                confidence="high",
                explanation="The available validation evidence rejects the value described by the claim.",
                evidence_refs=refs,
            )
        if rejection_evidence and any(
            word in lowered_claim for word in ("rejects", "rejected", "does not accept", "invalid")
        ):
            return EvidenceAssessment(
                claim=claim.text,
                assessment="supported",
                confidence="high",
                explanation="The available validation evidence rejects the value described by the claim.",
                evidence_refs=refs,
            )

        return EvidenceAssessment(
            claim=claim.text,
            assessment="uncertain",
            confidence="low",
            explanation="The offline analyzer found related evidence but cannot determine the claim reliably.",
            evidence_refs=refs,
        )
