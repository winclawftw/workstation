from dataclasses import dataclass
from .contracts import ModelProvider, ModelUnavailable

@dataclass(frozen=True)
class ModelReply:
    provider: str
    model: str | None
    text: str

class KeystoneEngine:
    def __init__(self, model_provider: ModelProvider):
        self.model_provider = model_provider

    def status(self) -> dict:
        return {"keystone": "ready", "provider": self.model_provider.name, "provider_health": self.model_provider.health()}

    def available_models(self) -> list[str]:
        return self.model_provider.list_models()

    def respond(self, prompt: str, *, model: str | None = None, history: list[dict[str, str]] | None = None, system_prompt: str | None = None) -> ModelReply:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        for item in history or []:
            if isinstance(item, dict) and item.get("role") in {"user", "assistant"} and isinstance(item.get("content"), str) and item["content"].strip():
                messages.append({"role": item["role"], "content": item["content"]})
        messages.append({"role": "user", "content": prompt.strip()})
        fn = getattr(self.model_provider, "generate_messages", None)
        text = fn(messages, model=model) if callable(fn) else self.model_provider.generate(prompt.strip(), model=model)
        if not isinstance(text, str) or not text.strip():
            raise ModelUnavailable("Model provider returned an empty response")
        return ModelReply(self.model_provider.name, model, text.strip())
