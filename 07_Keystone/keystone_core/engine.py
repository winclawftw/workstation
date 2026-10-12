"""Minimal Keystone orchestration core: request in, model response out.

This layer deliberately does not execute tools, access the filesystem, or use cloud
fallbacks. Model output is data, not authority.
"""
from dataclasses import dataclass
from .contracts import ModelProvider, ModelUnavailable


@dataclass(frozen=True)
class ModelReply:
    provider: str
    model: str | None
    text: str


class KeystoneEngine:
    """Small, injectable orchestration boundary around a ModelProvider."""

    def __init__(self, model_provider: ModelProvider):
        self.model_provider = model_provider

    def status(self) -> dict:
        health = self.model_provider.health()
        return {
            "keystone": "ready",
            "provider": self.model_provider.name,
            "provider_health": health,
        }

    def available_models(self) -> list[str]:
        return self.model_provider.list_models()

    def respond(self, prompt: str, *, model: str | None = None) -> ModelReply:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        text = self.model_provider.generate(prompt.strip(), model=model)
        if not isinstance(text, str) or not text.strip():
            raise ModelUnavailable("Model provider returned an empty response")
        return ModelReply(
            provider=self.model_provider.name,
            model=model,
            text=text.strip(),
        )
