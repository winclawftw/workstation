import json
import urllib.error
import urllib.request
from typing import Any

from .contracts import ModelProvider, ModelUnavailable

__all__ = ["ModelProvider", "OllamaModelProvider"]


class OllamaModelProvider:
    name = "ollama"

    def __init__(self, base_url: str = "http://127.0.0.1:11434", default_model: str = "llama3.2:3b", timeout: float = 10):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout

    def _get(self, path: str) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(self.base_url + path, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise ModelUnavailable(str(exc)) from exc

    def capabilities(self) -> set[str]:
        return {"local", "generate", "list_models", "health"}

    def health(self) -> dict[str, Any]:
        result = self._get("/api/version")
        return {"status": "ok", "provider": self.name, "version": result.get("version")}

    def list_models(self) -> list[str]:
        return [item["name"] for item in self._get("/api/tags").get("models", [])]

    def generate(self, prompt: str, *, model: str | None = None) -> str:
        payload = json.dumps({"model": model or self.default_model, "prompt": prompt, "stream": False}).encode()
        request = urllib.request.Request(self.base_url + "/api/generate", data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=max(self.timeout, 120)) as response:
                body = json.loads(response.read().decode("utf-8"))
                return str(body["response"])
        except (OSError, urllib.error.URLError, json.JSONDecodeError, KeyError) as exc:
            raise ModelUnavailable(str(exc)) from exc
