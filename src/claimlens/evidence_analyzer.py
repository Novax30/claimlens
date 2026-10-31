"""Use a local code model to assess a claim against collected evidence."""

from dataclasses import dataclass
from typing import List

from .claim_extractor import Claim
from .evidence_collector import Evidence
from .ollama_client import OllamaClient


@dataclass(frozen=True)
class EvidenceAssessment:
    claim: str
    assessment: str
    confidence: str
    explanation: str
    evidence_refs: List[str]
    execution_status: str = "not_attempted"


class EvidenceAnalyzer:
    def __init__(self, client: OllamaClient) -> None:
        self.client = client

    def analyze(self, claim: Claim, evidence: List[Evidence]) -> EvidenceAssessment:
        if not evidence:
            return EvidenceAssessment(
                claim=claim.text,
                assessment="uncertain",
                confidence="low",
                explanation="No relevant project evidence was found.",
                evidence_refs=[],
            )

        evidence_text = "\n".join(
            f"[{item.category}] {item.file}:{item.line} - {item.text}" for item in evidence
        )
        valid_refs = {f"{item.file}:{item.line}" for item in evidence}
        response = self.client.chat_json(
            system=(
                "Assess one technical claim using only the supplied evidence. "
                "Return JSON with assessment, confidence, explanation, and "
                "evidence_refs. evidence_refs must contain only exact file:line "
                "references from the supplied evidence. "
                "assessment must be supported, contradicted, or uncertain. "
                "confidence must be high, medium, or low. Never infer facts not "
                "present in the evidence. Prefer uncertain when evidence is weak. "
                "If there is no exact supporting reference, use uncertain."
            ),
            user=f"Claim: {claim.text}\nEvidence:\n{evidence_text}",
        )

        assessment = response.get("assessment")
        confidence = response.get("confidence")
        explanation = response.get("explanation")
        raw_refs = response.get("evidence_refs", [])
        evidence_refs = [ref for ref in raw_refs if ref in valid_refs] if isinstance(raw_refs, list) else []
        if assessment not in {"supported", "contradicted", "uncertain"}:
            assessment = "uncertain"
        if confidence not in {"high", "medium", "low"}:
            confidence = "low"
        if not isinstance(explanation, str) or not explanation.strip():
            explanation = "The model did not provide a usable explanation."
        if assessment != "uncertain" and not evidence_refs:
            assessment = "uncertain"
            confidence = "low"
            explanation = "The model did not cite exact supplied evidence for this assessment."

        deterministic = _deterministic_signal(claim.text, evidence)
        if deterministic is not None:
            assessment, explanation, evidence_refs = deterministic
            confidence = "high"

        return EvidenceAssessment(
            claim=claim.text,
            assessment=assessment,
            confidence=confidence,
            explanation=explanation.strip(),
            evidence_refs=evidence_refs,
        )


def _deterministic_signal(claim_text: str, evidence: List[Evidence]):
    """Override obvious model mistakes using direct validation language."""
    claim = claim_text.lower()
    rejection_markers = (
        "raise valueerror",
        "raise typeerror",
        "rejected",
        "must be greater than zero",
    )
    rejection_evidence = [
        item for item in evidence if any(marker in item.text.lower() for marker in rejection_markers)
    ]
    if not rejection_evidence:
        return None

    claims_acceptance = any(
        phrase in claim for phrase in ("accepts", "accepted", "allows", "allow", "is valid")
    )
    claims_rejection = any(
        phrase in claim for phrase in ("rejects", "rejected", "does not accept", "invalid")
    )
    refs = [f"{item.file}:{item.line}" for item in rejection_evidence]
    if claims_acceptance:
        return (
            "contradicted",
            "Direct validation evidence rejects the value described by the claim.",
            refs,
        )
    if claims_rejection:
        return (
            "supported",
            "Direct validation evidence rejects the value described by the claim.",
            refs,
        )
    return None
