from pathlib import Path
from typing import Any

from .contracts import ToolProvider, ToolUnavailable

__all__ = ["ToolProvider", "ReadOnlyToolProvider"]


class ReadOnlyToolProvider:
    name = "readonly"

    def list_tools(self) -> list[dict[str, Any]]:
        return [{"name": "get_current_directory", "read_only": True, "arguments": {}}]

    def get_tool(self, name: str) -> dict[str, Any]:
        for tool in self.list_tools():
            if tool["name"] == name:
                return tool
        raise ToolUnavailable(name)

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> str:
        self.get_tool(name)
        if arguments:
            raise ToolUnavailable("get_current_directory accepts no arguments")
        return str(Path.cwd())

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "provider": self.name, "tools": [t["name"] for t in self.list_tools()]}
