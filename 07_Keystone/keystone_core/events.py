from collections.abc import Callable
from typing import Any

from .domain import Event
from .storage import LocalStorage


class EventBus:
    def __init__(self, storage: LocalStorage):
        self.storage = storage
        self._subscribers: dict[str, list[Callable[[Event], None]]] = {}

    def subscribe(self, name: str, callback: Callable[[Event], None]) -> None:
        self._subscribers.setdefault(name, []).append(callback)

    def publish(self, name: str, **data: Any) -> Event:
        event = Event(name=name, data=data)
        self.storage.save("events", event)
        for callback in self._subscribers.get(name, []):
            callback(event)
        return event


class AuditLogger:
    def __init__(self, storage: LocalStorage):
        self.storage = storage

    def record(self, action: str, **data: Any) -> None:
        self.storage.save("audit", {"action": action, "data": data})
