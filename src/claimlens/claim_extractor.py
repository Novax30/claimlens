"""Extract simple, inspectable claims from an issue or pull request."""

from dataclasses import dataclass
import re
from typing import List

from .input_reader import ReportInput


@dataclass(frozen=True)
class Claim:
    text: str
    claim_type: str


def _claim_type(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("default", "config", "configuration", "setting", "timeout")):
        return "configuration"
    if any(word in lowered for word in ("docs", "documentation", "readme")):
        return "documentation"
    if any(word in lowered for word in ("security", "vulnerability", "exploit")):
        return "security"
    return "behavior"


def extract_claims(report: ReportInput) -> List[Claim]:
    """Split a report into non-empty claim sentences.

    This small deterministic version is used as a reliable fallback and as a
    testable baseline before adding local-model extraction.
    """
    text = f"{report.title}. {report.body}"
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    claims: List[Claim] = []
    seen = set()
    for sentence in sentences:
        cleaned = sentence.strip(" .!?\n\t")
        key = cleaned.casefold()
        if cleaned and key not in seen:
            claims.append(Claim(text=cleaned, claim_type=_claim_type(cleaned)))
            seen.add(key)
    return claims
