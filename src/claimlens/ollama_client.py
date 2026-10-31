"""Small client for the Ollama service running on the local machine."""

import json
from typing import Any, Callable, Dict, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen


class OllamaError(RuntimeError):
    """Raised when the local Ollama service cannot answer a request."""


class OllamaClient:
    def __init__(
        self,
        model: str,
        host: str = "http://127.0.0.1:11434",
        timeout: int = 120,
        opener: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.model = model
        self.endpoint = f"{host.rstrip('/')}/api/chat"
        self.timeout = timeout
        self._opener = opener or urlopen

    def chat_json(self, system: str, user: str) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "seed": 42},
        }
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError) as exc:
            raise OllamaError(f"could not contact local Ollama: {exc}") from exc

        content = result.get("message", {}).get("content")
        if not isinstance(content, str):
            raise OllamaError("Ollama response did not contain message content")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OllamaError("Ollama returned content that was not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise OllamaError("Ollama JSON response must be an object")
        return parsed
