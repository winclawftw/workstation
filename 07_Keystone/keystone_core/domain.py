from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    description: str = ""
    status: str = "active"
    created_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class Task:
    id: str
    project_id: str
    title: str
    status: str = "pending"
    created_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class Agent:
    id: str
    name: str
    runtime: str
    status: str = "ready"


@dataclass(frozen=True)
class Job:
    id: str
    task_id: str
    status: str = "queued"
    created_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class Approval:
    id: str
    action: str
    status: str
    reason: str
    created_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class Event:
    name: str
    data: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now_iso)
    id: str = field(default_factory=lambda: new_id("evt"))


@dataclass(frozen=True)
class Artifact:
    id: str
    type: str
    reference: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now_iso)
