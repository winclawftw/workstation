"""OpenAI-compatible adapter for the local Bonsai llama.cpp server."""

import json
import urllib.error
import urllib.request
from typing import Any

from .contracts import ModelProvider, ModelUnavailable

__all__ = ["BonsaiModelProvider"]


class BonsaiModelProvider:
    """Text-only ModelProvider adapter; never executes model-proposed tools."""

    name = "bonsai"

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        default_model: str = "bonsai2-gguf/27B",
        timeout: float = 10,
        generation_timeout: float = 120,
    ):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        self.generation_timeout = generation_timeout

    def _request_json(
        self,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers=headers,
            method="POST" if data is not None else "GET",
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self.timeout if timeout is None else timeout
            ) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (
            OSError,
            urllib.error.URLError,
            json.JSONDecodeError,
            UnicodeDecodeError,
        ) as exc:
            raise ModelUnavailable(
                f"Bonsai request failed ({type(exc).__name__}) for {path}"
            ) from exc

        if not isinstance(body, dict):
            raise ModelUnavailable(f"Bonsai returned an invalid JSON object for {path}")
        return body

    def capabilities(self) -> set[str]:
        return {"local", "generate", "generate_messages", "list_models", "health"}

    def health(self) -> dict[str, Any]:
        result = self._request_json("/health")
        if result.get("status") != "ok":
            raise ModelUnavailable("Bonsai health endpoint did not report status=ok")
        return {
            "status": "ok",
            "provider": self.name,
            "model": self.default_model,
        }

    def list_models(self) -> list[str]:
        result = self._request_json("/v1/models")
        models = result.get("data")
        if not isinstance(models, list):
            raise ModelUnavailable("Bonsai model listing did not contain a data list")
        return [
            item["id"]
            for item in models
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]

    def generate(self, prompt: str, *, model: str | None = None) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        return self.generate_messages(
            [{"role": "user", "content": prompt.strip()}], model=model
        )

    def generate_messages(
        self, messages: list[dict[str, str]], *, model: str | None = None
    ) -> str:
        """Generate from a validated chat history, preserving role and order."""
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages must be a non-empty list")
        allowed_roles = {"system", "user", "assistant"}
        safe_messages: list[dict[str, str]] = []
        for message in messages:
            if not isinstance(message, dict):
                raise ValueError("each message must be an object")
            role, content = message.get("role"), message.get("content")
            if role not in allowed_roles or not isinstance(content, str) or not content.strip():
                raise ValueError("messages require an allowed role and non-empty content")
            safe_messages.append({"role": role, "content": content})

        result = self._request_json(
            "/v1/chat/completions",
            payload={
                "model": model or self.default_model,
                "messages": safe_messages,
                "stream": False,
            },
            timeout=max(self.timeout, self.generation_timeout),
        )
        choices = result.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ModelUnavailable("Bonsai completion did not contain a valid choice")
        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise ModelUnavailable("Bonsai completion did not contain a message")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ModelUnavailable("Bonsai returned no user-facing message content")
        return content
