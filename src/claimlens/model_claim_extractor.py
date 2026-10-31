"""Claim extraction using a local open-weight model through Ollama."""

from typing import List

from .claim_extractor import Claim
from .input_reader import ReportInput
from .ollama_client import OllamaClient


class ModelClaimExtractor:
    def __init__(self, client: OllamaClient) -> None:
        self.client = client

    def extract_claims(self, report: ReportInput) -> List[Claim]:
        response = self.client.chat_json(
            system=(
                "Extract only technical claims from the report. "
                "Return JSON with a claims array. Each item must have text and "
                "claim_type, where claim_type is configuration, documentation, "
                "security, or behavior. Do not invent claims."
            ),
            user=f"Type: {report.kind}\nTitle: {report.title}\nBody: {report.body}",
        )
        raw_claims = response.get("claims", [])
        if not isinstance(raw_claims, list):
            return []

        claims: List[Claim] = []
        seen = set()
        allowed_types = {"configuration", "documentation", "security", "behavior"}
        for item in raw_claims:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            claim_type = item.get("claim_type")
            if not isinstance(text, str) or not text.strip():
                continue
            if claim_type not in allowed_types:
                claim_type = "behavior"
            normalized = text.strip()
            if normalized.casefold() in seen:
                continue
            claims.append(Claim(text=normalized, claim_type=claim_type))
            seen.add(normalized.casefold())
        return claims
