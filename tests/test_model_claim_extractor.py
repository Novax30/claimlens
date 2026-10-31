import json

from claimlens.input_reader import ReportInput
from claimlens.model_claim_extractor import ModelClaimExtractor
from claimlens.ollama_client import OllamaClient, OllamaError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def fake_opener(request, timeout):
    assert request.full_url.endswith("/api/chat")
    assert timeout == 10
    return FakeResponse(
        {
            "message": {
                "content": json.dumps(
                    {
                        "claims": [
                            {"text": "Negative timeout values are rejected", "claim_type": "configuration"},
                            {"text": "Negative timeout values are rejected", "claim_type": "configuration"},
                        ]
                    }
                )
            }
        }
    )


def test_ollama_client_and_model_extractor_parse_structured_claims():
    client = OllamaClient("qwen2.5:7b", timeout=10, opener=fake_opener)
    extractor = ModelClaimExtractor(client)

    claims = extractor.extract_claims(
        ReportInput("Timeout issue", "Negative timeout values are rejected.")
    )

    assert len(claims) == 1
    assert claims[0].claim_type == "configuration"


def test_model_extractor_ignores_malformed_items():
    def malformed_opener(request, timeout):
        return FakeResponse({"message": {"content": '{"claims": [null, {"text": ""}]}'}})

    extractor = ModelClaimExtractor(OllamaClient("qwen2.5:7b", opener=malformed_opener))

    assert extractor.extract_claims(ReportInput("Title", "Body")) == []


def test_ollama_client_rejects_non_json_content():
    def bad_opener(request, timeout):
        return FakeResponse({"message": {"content": "not json"}})

    client = OllamaClient("qwen2.5:7b", opener=bad_opener)

    try:
        client.chat_json("system", "user")
    except OllamaError as error:
        assert "valid JSON" in str(error)
    else:
        raise AssertionError("expected OllamaError")
