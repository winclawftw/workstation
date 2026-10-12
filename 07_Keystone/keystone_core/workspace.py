"""Safe, local JSON workspace for Keystone projects and Markdown artifacts."""

from __future__ import annotations

import json
import os
import re
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


class WorkspaceError(ValueError):
    """A workspace operation was invalid or could not be completed safely."""


MAX_PROJECT_RECORD_BYTES = 1_000_000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalise_windows_path(path: str) -> str:
    if path.startswith("\\\\?\\UNC\\"):
        path = "\\\\" + path[8:]
    elif path.startswith("\\\\?\\"):
        path = path[4:]
    return os.path.normcase(os.path.normpath(path))


def _open_checked_windows_handle(
    path: Path, *, desired_access: int, flags: int, kind: str
) -> int:
    """Open final path component itself and verify its attributes and path."""
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = ctypes.c_void_p
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = wintypes.BOOL

    handle = create_file(
        str(path),
        desired_access,
        0x00000001 | 0x00000002,  # FILE_SHARE_READ | FILE_SHARE_WRITE
        None,
        3,  # OPEN_EXISTING
        flags,
        None,
    )
    if handle in (None, ctypes.c_void_p(-1).value):
        error = ctypes.get_last_error()
        if kind == "project record" and error in (2, 3):
            raise FileNotFoundError(error, os.strerror(error), str(path))
        raise WorkspaceError(
            f"{kind} could not be opened safely: {path.name} (Windows error {error})"
        )

    try:
        class FileAttributeTagInfo(ctypes.Structure):
            _fields_ = [("attributes", wintypes.DWORD), ("tag", wintypes.DWORD)]

        get_info = kernel32.GetFileInformationByHandleEx
        get_info.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        get_info.restype = wintypes.BOOL
        info = FileAttributeTagInfo()
        if not get_info(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            error = ctypes.get_last_error()
            raise WorkspaceError(
                f"{kind} could not be verified: {path.name} (Windows error {error})"
            )
        if info.attributes & 0x00000400:  # FILE_ATTRIBUTE_REPARSE_POINT
            message = (
                f"{kind} cannot be a link"
                if kind == "workspace directory"
                else f"{kind} cannot be a reparse point"
            )
            raise WorkspaceError(message)
        is_directory = bool(info.attributes & 0x00000010)  # FILE_ATTRIBUTE_DIRECTORY
        if (kind == "workspace directory") != is_directory:
            raise WorkspaceError(f"{kind} has an unexpected file type")

        get_final_path = kernel32.GetFinalPathNameByHandleW
        get_final_path.argtypes = [
            ctypes.c_void_p,
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        get_final_path.restype = wintypes.DWORD
        final_buffer = ctypes.create_unicode_buffer(32768)
        final_length = get_final_path(handle, final_buffer, len(final_buffer), 0)
        if not final_length or final_length >= len(final_buffer):
            error = ctypes.get_last_error()
            raise WorkspaceError(
                f"{kind} path could not be verified: {path.name} (Windows error {error})"
            )
        if _normalise_windows_path(final_buffer.value) != _normalise_windows_path(
            str(path.absolute())
        ):
            raise WorkspaceError(f"{kind} escapes workspace")
        return handle
    except Exception:
        close_handle(handle)
        raise


def _close_windows_handle(handle: int) -> None:
    import ctypes

    close_handle = ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = ctypes.c_int
    close_handle(handle)


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
        with self._guard_workspace_directory(self.root):
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

    @contextmanager
    def _guard_workspace_directory(self, path: Path) -> Iterator[None]:
        """Pin checked Windows directory against rename/replacement during I/O.

        Windows requires DELETE access on the directory handle, combined with
        a share mode that omits FILE_SHARE_DELETE, for rename attempts to fail
        with a sharing violation. OPEN_REPARSE_POINT lets us inspect the
        directory entry itself before trusting the handle.
        """
        self._ensure_workspace_directory(path)
        if os.name != "nt":
            # Other platforms retain existing path checks; Windows handle
            # semantics below are the supported protection for this project.
            yield
            return

        # DELETE access is deliberate: Windows otherwise allows a directory
        # rename even when a metadata-only handle omits FILE_SHARE_DELETE.
        handle = _open_checked_windows_handle(
            path,
            desired_access=0x00010000,  # DELETE
            flags=0x02000000 | 0x00200000,  # BACKUP_SEMANTICS | OPEN_REPARSE_POINT
            kind="workspace directory",
        )
        try:
            yield
        finally:
            _close_windows_handle(handle)

    @contextmanager
    def _open_project_file(self, path: Path) -> Iterator[Any]:
        """Open project JSON without following a final Windows reparse point."""
        if os.name != "nt":
            with path.open("rb") as stream:
                yield stream
            return

        import msvcrt
        handle = _open_checked_windows_handle(
            path,
            desired_access=0x80000000 | 0x00000080,  # GENERIC_READ | FILE_READ_ATTRIBUTES
            flags=0x00200000 | 0x02000000,  # OPEN_REPARSE_POINT | BACKUP_SEMANTICS
            kind="project record",
        )
        transferred = False
        try:
            fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
            transferred = True
            with os.fdopen(fd, "rb") as stream:
                yield stream
        finally:
            if not transferred:
                _close_windows_handle(handle)

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
        with self._guard_workspace_directory(self.projects_dir):
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
        self.last_list_warnings = []
        items = []
        with self._guard_workspace_directory(self.projects_dir):
            for path in self.projects_dir.glob("*.json"):
                if self._is_link_or_junction(path):
                    self.last_list_warnings.append(
                        f"{path.name}: linked project records are ignored"
                    )
                    continue
                try:
                    item = self._read_project_file(path, directory_guarded=True)
                except WorkspaceError as exc:
                    self.last_list_warnings.append(f"{path.name}: {exc}")
                    continue
                items.append(item)
        return sorted(
            items,
            key=lambda item: str(item.get("updated_at", "")),
            reverse=True,
        )

    def _read_project_file(
        self, path: Path, *, directory_guarded: bool = False
    ) -> dict[str, Any]:
        if path.parent != self.projects_dir:
            raise WorkspaceError("Project path escapes workspace")
        if not directory_guarded:
            with self._guard_workspace_directory(self.projects_dir):
                return self._read_project_file(path, directory_guarded=True)
        try:
            with self._open_project_file(path) as stream:
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
        with self._guard_workspace_directory(self.artifacts_dir):
            return self._create_artifact_file_guarded(requested_name, content)

    def _create_artifact_file_guarded(self, requested_name: str, content: str) -> Path:
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
        with self._guard_workspace_directory(self.artifacts_dir):
            path = self._create_artifact_file_guarded(name, content)
            if project is not None:
                project["artifacts"].append(
                    {
                        "filename": path.name,
                        "path": str(path),
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
