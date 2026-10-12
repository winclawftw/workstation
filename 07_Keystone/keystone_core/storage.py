import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from .contracts import StorageFailed


class LocalStorage:
    """Small JSONL-backed storage adapter; replaceable without changing the core."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, collection: str) -> Path:
        if not collection.replace("_", "").isalnum():
            raise StorageFailed("invalid collection")
        return self.root / f"{collection}.jsonl"

    def save(self, collection: str, item: Any) -> None:
        try:
            value = asdict(item) if is_dataclass(item) else item
            with self._path(collection).open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(value, sort_keys=True) + "\n")
        except (OSError, TypeError, ValueError) as exc:
            raise StorageFailed(str(exc)) from exc

    def list(self, collection: str) -> list[Any]:
        path = self._path(collection)
        if not path.exists():
            return []
        try:
            return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageFailed(str(exc)) from exc

    def health(self) -> dict[str, Any]:
        probe = self.root / ".health"
        try:
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return {"status": "ok", "provider": "local"}
        except OSError as exc:
            raise StorageFailed(str(exc)) from exc
