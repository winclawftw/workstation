"""Safe, local JSON workspace for Keystone projects and Markdown artifacts."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class WorkspaceError(ValueError):
    """A workspace operation was invalid or could not be completed safely."""


MAX_PROJECT_RECORD_BYTES = 1_000_000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkspaceStore:
    """Persist projects as JSON and artifacts as UTF-8 Markdown files."""

    def __init__(self, root: str | Path):
        requested_root = Path(root).expanduser().absolute()
        for parent in (requested_root, *requested_root.parents):
            if self._is_link_or_junction(parent):
                raise WorkspaceError("Workspace data root cannot contain symlinks or junctions")
        self.root = requested_root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.projects_dir = self.root / "projects"
        self.artifacts_dir = self.root / "artifacts"
        self.last_list_warnings: list[str] = []
        self._ensure_workspace_directory(self.projects_dir)
        self._ensure_workspace_directory(self.artifacts_dir)

    @staticmethod
    def _is_link_or_junction(path: Path) -> bool:
        is_junction = getattr(path, "is_junction", None)
        return path.is_symlink() or (callable(is_junction) and is_junction())

    def _ensure_workspace_directory(self, path: Path) -> None:
        if self._is_link_or_junction(path):
            raise WorkspaceError(f"Workspace directory cannot be a link: {path.name}")
        try:
            path.mkdir(parents=True, exist_ok=True)
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise WorkspaceError(f"Workspace directory is unavailable: {path.name}") from exc
        if self._is_link_or_junction(path) or not resolved.is_relative_to(self.root):
            raise WorkspaceError(f"Workspace directory escapes data root: {path.name}")

    def _project_path(self, project_id: str) -> Path:
        if not isinstance(project_id, str) or not re.fullmatch(r"[a-f0-9]{12}", project_id):
            raise WorkspaceError("Invalid project ID")
        self._ensure_workspace_directory(self.projects_dir)
        path = self.projects_dir / f"{project_id}.json"
        if self._is_link_or_junction(path) or not path.resolve().is_relative_to(self.projects_dir):
            raise WorkspaceError("Project path escapes workspace")
        return path

    def create_project(self, name: str, description: str = "") -> dict[str, Any]:
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
            raise WorkspaceError("Enter a project name (1 to 120 characters)")
        if not isinstance(description, str) or len(description) > 4000:
            raise WorkspaceError("Description must be text of at most 4000 characters")

        while True:
            project_id = uuid.uuid4().hex[:12]
            if not self._project_path(project_id).exists():
                break
        now = _now_iso()
        item = {
            "id": project_id,
            "name": name.strip(),
            "description": description.strip(),
            "created_at": now,
            "updated_at": now,
            "notes": [],
            "artifacts": [],
        }
        self._write(item)
        return item

    def _write(self, item: dict[str, Any]) -> None:
        path = self._project_path(item.get("id"))
        temporary = self.projects_dir / f".{item['id']}.{uuid.uuid4().hex}.tmp"
        try:
            payload = (json.dumps(item, ensure_ascii=False, indent=2) + "\n").encode(
                "utf-8"
            )
        except (TypeError, ValueError, UnicodeError) as exc:
            raise WorkspaceError("Project record could not be encoded safely") from exc
        if len(payload) > MAX_PROJECT_RECORD_BYTES:
            raise WorkspaceError("Project record exceeds 1 MB")
        try:
            with temporary.open("xb") as stream:
                stream.write(payload)
            temporary.replace(path)
        except (OSError, TypeError, ValueError) as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise WorkspaceError("Project could not be saved safely") from exc

    def list_projects(self) -> list[dict[str, Any]]:
        self._ensure_workspace_directory(self.projects_dir)
        self.last_list_warnings = []
        items = []
        for path in self.projects_dir.glob("*.json"):
            if self._is_link_or_junction(path):
                self.last_list_warnings.append(
                    f"{path.name}: linked project records are ignored"
                )
                continue
            try:
                item = self._read_project_file(path)
            except WorkspaceError as exc:
                self.last_list_warnings.append(f"{path.name}: {exc}")
                continue
            items.append(item)
        return sorted(
            items,
            key=lambda item: str(item.get("updated_at", "")),
            reverse=True,
        )

    def _read_project_file(self, path: Path) -> dict[str, Any]:
        try:
            with path.open("rb") as stream:
                payload = stream.read(MAX_PROJECT_RECORD_BYTES + 1)
            if len(payload) > MAX_PROJECT_RECORD_BYTES:
                raise WorkspaceError("Project record exceeds 1 MB")
            item = json.loads(payload.decode("utf-8"))
        except FileNotFoundError as exc:
            raise WorkspaceError(f"Project not found: {path.stem}") from exc
        except (OSError, json.JSONDecodeError, UnicodeDecodeError, RecursionError) as exc:
            raise WorkspaceError("Project record is unreadable") from exc
        if not isinstance(item, dict) or item.get("id") != path.stem:
            raise WorkspaceError("Invalid project record")
        text_fields = ("name", "description", "created_at", "updated_at")
        if any(not isinstance(item.get(field), str) for field in text_fields):
            raise WorkspaceError("Invalid project record")
        notes = item.get("notes")
        artifacts = item.get("artifacts")
        if not isinstance(notes, list) or not isinstance(artifacts, list):
            raise WorkspaceError("Invalid project record")
        if any(
            not isinstance(note, dict)
            or not isinstance(note.get("text"), str)
            or not isinstance(note.get("created_at"), str)
            for note in notes
        ):
            raise WorkspaceError("Invalid project record")
        if any(
            not isinstance(artifact, dict)
            or not isinstance(artifact.get("filename"), str)
            or not isinstance(artifact.get("path"), str)
            or not isinstance(artifact.get("saved_at"), str)
            for artifact in artifacts
        ):
            raise WorkspaceError("Invalid project record")
        return item

    def get_project(self, project_id: str) -> dict[str, Any]:
        path = self._project_path(project_id)
        return self._read_project_file(path)

    def add_note(self, project_id: str, note: str) -> dict[str, Any]:
        if not isinstance(note, str) or not note.strip() or len(note) > 12000:
            raise WorkspaceError("Note must contain 1 to 12000 characters")
        item = self.get_project(project_id)
        item["notes"].append({"text": note.strip(), "created_at": _now_iso()})
        item["updated_at"] = _now_iso()
        self._write(item)
        return item

    def _validated_artifact_name(self, filename: str) -> str:
        if not isinstance(filename, str) or not filename.strip():
            raise WorkspaceError("A filename is required")
        name = filename.strip()
        if not name.lower().endswith(".md"):
            name += ".md"
        if (
            Path(name).name != name
            or Path(name).is_absolute()
            or not re.fullmatch(r"[\w .()-]+\.md", name, re.IGNORECASE)
        ):
            raise WorkspaceError("Use a filename only, without folders")
        return name

    def _create_artifact_file(self, requested_name: str, content: str) -> Path:
        self._ensure_workspace_directory(self.artifacts_dir)
        requested = Path(requested_name)
        stem = requested.stem
        suffix = requested.suffix
        number = 1
        while number <= 10000:
            name = requested_name if number == 1 else f"{stem} ({number}){suffix}"
            path = self.artifacts_dir / name
            created = False
            try:
                with path.open("x", encoding="utf-8", newline="\n") as stream:
                    created = True
                    stream.write(content.rstrip() + "\n")
                return path
            except FileExistsError:
                number += 1
            except OSError as exc:
                if created:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass
                raise WorkspaceError("Artifact could not be written safely") from exc
        raise WorkspaceError("Could not find an unused artifact filename")

    def save_artifact(
        self,
        filename: str,
        content: str,
        project_id: str | None = None,
    ) -> Path:
        if not isinstance(content, str) or not content.strip():
            raise WorkspaceError("Artifact content must not be empty")
        if len(content.encode("utf-8")) > 200000:
            raise WorkspaceError("Artifact exceeds 200 KB")

        name = self._validated_artifact_name(filename)
        project = self.get_project(project_id) if project_id is not None else None
        path = self._create_artifact_file(name, content)
        if project is not None:
            project["artifacts"].append(
                {
                    "filename": path.name,
                    "path": str(path.resolve()),
                    "saved_at": _now_iso(),
                }
            )
            project["updated_at"] = _now_iso()
            try:
                self._write(project)
            except WorkspaceError:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
        return path
