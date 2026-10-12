from dataclasses import dataclass
from typing import Any, Protocol


class KeystoneError(Exception):
    """Base error with a stable category for observability."""


class RuntimeUnavailable(KeystoneError): pass
class ModelUnavailable(KeystoneError): pass
class ToolUnavailable(KeystoneError): pass
class PolicyDenied(KeystoneError): pass
class ApprovalRequired(KeystoneError): pass
class ExecutionFailed(KeystoneError): pass
class StorageFailed(KeystoneError): pass


class AgentRuntime(Protocol):
    name: str
    version: str

    def capabilities(self) -> set[str]: ...
    def health(self) -> dict[str, Any]: ...
    def run(self, prompt: str, *, model: str | None = None) -> str: ...


class ModelProvider(Protocol):
    name: str

    def capabilities(self) -> set[str]: ...
    def health(self) -> dict[str, Any]: ...
    def list_models(self) -> list[str]: ...
    def generate(self, prompt: str, *, model: str | None = None) -> str: ...


class ToolProvider(Protocol):
    name: str

    def list_tools(self) -> list[dict[str, Any]]: ...
    def get_tool(self, name: str) -> dict[str, Any]: ...
    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> Any: ...


class StorageProvider(Protocol):
    def save(self, collection: str, item: Any) -> None: ...
    def list(self, collection: str) -> list[Any]: ...


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    required: bool
    reason: str
