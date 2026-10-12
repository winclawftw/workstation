import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from keystone_core.workspace import (
    MAX_PROJECT_RECORD_BYTES,
    WorkspaceError,
    WorkspaceStore,
)


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = WorkspaceStore(Path(self.temp.name) / "data")

    def _create_junction(self, link: Path, target: Path) -> None:
        if sys.platform != "win32":
            self.skipTest("Windows junction checks require Windows")
        env = os.environ.copy()
        env["KEYSTONE_JUNCTION_LINK"] = str(link)
        env["KEYSTONE_JUNCTION_TARGET"] = str(target)
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "New-Item -ItemType Junction -Path $env:KEYSTONE_JUNCTION_LINK "
                "-Target $env:KEYSTONE_JUNCTION_TARGET | Out-Null",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode:
            self.skipTest(
                "Junction creation unavailable: " + (result.stderr or result.stdout)
            )

    def test_project_and_note_persist(self):
        item = self.store.create_project("Doenerladen Konzept")
        self.assertEqual(self.store.get_project(item["id"])["name"], item["name"])
        changed = self.store.add_note(item["id"], "Anthrazit und Orange")
        self.assertEqual(changed["notes"][0]["text"], "Anthrazit und Orange")
        self.assertEqual(self.store.list_projects()[0]["id"], item["id"])
        restarted = WorkspaceStore(Path(self.temp.name) / "data")
        reloaded = restarted.get_project(item["id"])
        self.assertEqual(reloaded["notes"][0]["text"], "Anthrazit und Orange")

    def test_artifact_is_written_and_linked(self):
        item = self.store.create_project("Konzept")
        path = self.store.save_artifact("konzept.md", "# Entwurf\nText", item["id"])
        self.assertEqual(path.parent, self.store.artifacts_dir)
        self.assertIn("# Entwurf", path.read_text(encoding="utf-8"))
        self.assertEqual(self.store.get_project(item["id"])["artifacts"][0]["filename"], "konzept.md")

    def test_artifact_collision_preserves_both_files(self):
        first = self.store.save_artifact("konzept.md", "Erster Entwurf")
        second = self.store.save_artifact("konzept.md", "Zweiter Entwurf")
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_text(encoding="utf-8"), "Erster Entwurf\n")
        self.assertEqual(second.read_text(encoding="utf-8"), "Zweiter Entwurf\n")

    def test_artifact_hardlink_collision_does_not_modify_external_file(self):
        outside = Path(self.temp.name) / "outside-linked.md"
        outside.write_text("extern geschützt", encoding="utf-8")
        linked = self.store.artifacts_dir / "linked.md"
        linked.hardlink_to(outside)

        saved = self.store.save_artifact("linked.md", "neue Workspace-Datei")

        self.assertEqual(saved.name, "linked (2).md")
        self.assertEqual(outside.read_text(encoding="utf-8"), "extern geschützt")
        self.assertEqual(linked.read_text(encoding="utf-8"), "extern geschützt")

    def test_invalid_project_does_not_leave_orphan_artifact(self):
        with self.assertRaises(WorkspaceError):
            self.store.save_artifact("orphan.md", "Inhalt", "not-an-id")
        self.assertFalse((self.store.artifacts_dir / "orphan.md").exists())

    def test_artifact_filename_cannot_escape_workspace(self):
        outside = Path(self.temp.name) / "outside.md"
        with self.assertRaises(WorkspaceError):
            self.store.save_artifact("..\\outside.md", "Inhalt")
        self.assertFalse(outside.exists())

    def test_artifact_limit_counts_utf8_bytes(self):
        content = "é" * 100001
        with self.assertRaises(WorkspaceError):
            self.store.save_artifact("large.md", content)
        self.assertFalse((self.store.artifacts_dir / "large.md").exists())

    def test_malformed_project_schema_returns_workspace_error(self):
        item = self.store.create_project("Beschädigter Datensatz")
        path = self.store.projects_dir / f"{item['id']}.json"
        path.write_text(
            json.dumps({**item, "notes": ["not a note object"]}), encoding="utf-8"
        )
        with self.assertRaises(WorkspaceError):
            self.store.get_project(item["id"])

    def test_malformed_json_returns_workspace_error_without_changing_file(self):
        item = self.store.create_project("Beschädigtes JSON")
        path = self.store.projects_dir / f"{item['id']}.json"
        path.write_text('{"id":', encoding="utf-8")
        original = path.read_bytes()

        with self.assertRaises(WorkspaceError):
            self.store.get_project(item["id"])

        self.assertEqual(path.read_bytes(), original)

    def test_deeply_nested_json_returns_workspace_error(self):
        item = self.store.create_project("Tief verschachtelt")
        path = self.store.projects_dir / f"{item['id']}.json"
        path.write_text("[" * 2000 + "0" + "]" * 2000, encoding="utf-8")

        with self.assertRaises(WorkspaceError):
            self.store.get_project(item["id"])

    def test_oversized_project_json_is_rejected_with_bounded_read(self):
        item = self.store.create_project("Zu groß")
        path = self.store.projects_dir / f"{item['id']}.json"
        path.write_bytes(b" " * (MAX_PROJECT_RECORD_BYTES + 1))
        original_size = path.stat().st_size

        with self.assertRaises(WorkspaceError):
            self.store.get_project(item["id"])

        self.assertEqual(path.stat().st_size, original_size)

    def test_oversized_project_write_preserves_existing_record(self):
        item = self.store.create_project("Geschützt")
        original = self.store.get_project(item["id"])
        oversized = {**item, "extra": "x" * MAX_PROJECT_RECORD_BYTES}

        with self.assertRaises(WorkspaceError):
            self.store._write(oversized)

        self.assertEqual(self.store.get_project(item["id"]), original)
        self.assertEqual(list(self.store.projects_dir.glob("*.tmp")), [])

    def test_project_replace_does_not_modify_external_hardlink_target(self):
        item = self.store.create_project("Hardlink-Test")
        record = self.store.projects_dir / f"{item['id']}.json"
        outside = Path(self.temp.name) / "outside-project.json"
        original = record.read_bytes()
        outside.write_bytes(original)
        record.unlink()
        record.hardlink_to(outside)

        changed = {**item, "description": "aktualisiert"}
        self.store._write(changed)

        self.assertEqual(outside.read_bytes(), original)
        self.assertEqual(self.store.get_project(item["id"])["description"], "aktualisiert")

    def test_list_projects_reports_corrupt_and_oversized_records(self):
        item = self.store.create_project("Gültiges Projekt")
        corrupt = self.store.projects_dir / "corrupt.json"
        corrupt.write_text('{"id":', encoding="utf-8")
        oversized = self.store.projects_dir / "oversized.json"
        oversized.write_bytes(b" " * (MAX_PROJECT_RECORD_BYTES + 1))

        projects = self.store.list_projects()

        self.assertEqual([project["id"] for project in projects], [item["id"]])
        self.assertEqual(len(self.store.last_list_warnings), 2)
        self.assertTrue(
            any("corrupt.json" in warning for warning in self.store.last_list_warnings)
        )
        self.assertTrue(
            any("oversized.json" in warning for warning in self.store.last_list_warnings)
        )

    def test_junctioned_projects_directory_is_rejected_without_admin(self):
        outside = Path(self.temp.name) / "outside-projects"
        outside.mkdir()
        sentinel = outside / "keep.txt"
        sentinel.write_text("geschützt", encoding="utf-8")
        projects = self.store.projects_dir
        projects.rmdir()
        self._create_junction(projects, outside)

        self.assertTrue(projects.is_junction())
        with self.assertRaises(WorkspaceError):
            WorkspaceStore(self.store.root)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "geschützt")

    def test_junctioned_artifacts_directory_is_rejected_without_admin(self):
        outside = Path(self.temp.name) / "outside-artifacts"
        outside.mkdir()
        sentinel = outside / "keep.txt"
        sentinel.write_text("geschützt", encoding="utf-8")
        artifacts = self.store.artifacts_dir
        artifacts.rmdir()
        self._create_junction(artifacts, outside)

        self.assertTrue(artifacts.is_junction())
        with self.assertRaises(WorkspaceError):
            self.store.save_artifact("escape.md", "nicht schreiben")
        self.assertFalse((outside / "escape.md").exists())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "geschützt")

    def test_artifacts_junction_inserted_after_path_check_is_rejected(self):
        outside = Path(self.temp.name) / "outside-race"
        outside.mkdir()
        sentinel = outside / "keep.txt"
        sentinel.write_text("geschützt", encoding="utf-8")
        artifacts = self.store.artifacts_dir
        ensure = self.store._ensure_workspace_directory
        inserted = False

        def replace_after_check(path):
            nonlocal inserted
            ensure(path)
            if path == artifacts and not inserted:
                inserted = True
                artifacts.rmdir()
                self._create_junction(artifacts, outside)

        with patch.object(self.store, "_ensure_workspace_directory", replace_after_check):
            with self.assertRaisesRegex(WorkspaceError, "link"):
                self.store.save_artifact("race.md", "darf nicht nach außen")

        self.assertTrue(inserted)
        self.assertFalse((outside / "race.md").exists())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "geschützt")

    def test_artifacts_directory_cannot_be_exchanged_after_guard_is_open(self):
        outside = Path(self.temp.name) / "outside-locked-race"
        outside.mkdir()
        (outside / "artifacts").mkdir()
        sentinel = outside / "keep.txt"
        sentinel.write_text("geschützt", encoding="utf-8")
        artifacts = self.store.artifacts_dir
        moved = Path(self.temp.name) / "moved-artifacts"
        moved_root = Path(self.temp.name) / "moved-data-root"
        real_open = Path.open
        attack = {"attempted": False, "blocked": False}

        def exchange_before_file_open(path, *args, **kwargs):
            if path.parent == artifacts and path.name == "race.md" and not attack["attempted"]:
                attack["attempted"] = True
                try:
                    os.rmdir(artifacts)
                except OSError as exc:
                    attack["rmdir_blocked"] = getattr(exc, "winerror", None) == 32
                else:
                    self._create_junction(artifacts, outside)
                try:
                    os.rename(artifacts, moved)
                except OSError as exc:
                    attack["blocked"] = getattr(exc, "winerror", None) == 32
                else:
                    # If the guard failed, complete the same junction attack;
                    # the assertions below must then fail on the external write.
                    self._create_junction(artifacts, outside)
                try:
                    os.rename(self.store.root, moved_root)
                except OSError as exc:
                    attack["root_blocked"] = getattr(exc, "winerror", None) in (5, 32)
                else:
                    self._create_junction(self.store.root, outside)
            return real_open(path, *args, **kwargs)

        with patch.object(Path, "open", exchange_before_file_open):
            saved = self.store.save_artifact("race.md", "bleibt im Workspace")

        self.assertTrue(attack["attempted"])
        self.assertTrue(attack["rmdir_blocked"], "Windows did not block directory removal")
        self.assertTrue(attack["blocked"], "Windows did not block directory rename")
        self.assertTrue(attack["root_blocked"], "Windows did not block workspace-root rename")
        self.assertEqual(saved.parent, artifacts)
        self.assertEqual(saved.read_text(encoding="utf-8"), "bleibt im Workspace\n")
        self.assertFalse((outside / "race.md").exists())
        self.assertFalse((outside / "artifacts" / "race.md").exists())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "geschützt")

    def test_projects_junction_inserted_after_path_check_is_rejected(self):
        outside = Path(self.temp.name) / "outside-project-race"
        outside.mkdir()
        projects = self.store.projects_dir
        ensure = self.store._ensure_workspace_directory
        calls = 0

        def replace_after_guard_check(path):
            nonlocal calls
            ensure(path)
            if path == projects:
                calls += 1
                # create_project checks the ID, _write checks it again, then
                # _guard_workspace_directory performs the final path check.
                if calls == 3:
                    projects.rmdir()
                    self._create_junction(projects, outside)

        with patch.object(self.store, "_ensure_workspace_directory", replace_after_guard_check):
            with self.assertRaisesRegex(WorkspaceError, "link"):
                self.store.create_project("Race-Test")

        self.assertFalse(list(outside.iterdir()))

    def test_project_file_symlink_is_not_read(self):
        outside = Path(self.temp.name) / "outside-project.json"
        outside.write_text('{"secret":"external"}', encoding="utf-8")
        item = self.store.create_project("Symlink-Test")
        record = self.store.projects_dir / f"{item['id']}.json"
        record.unlink()
        try:
            record.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"File symlink unavailable on this Windows configuration: {exc}")

        with self.assertRaises(WorkspaceError):
            self.store.get_project(item["id"])
        self.assertEqual(outside.read_text(encoding="utf-8"), '{"secret":"external"}')

    def test_project_record_junction_is_rejected(self):
        outside = Path(self.temp.name) / "outside-project-record"
        outside.mkdir()
        sentinel = outside / "keep.json"
        sentinel.write_text('{"secret":"external"}', encoding="utf-8")
        item = self.store.create_project("Junction-Test")
        record = self.store.projects_dir / f"{item['id']}.json"
        record.unlink()
        self._create_junction(record, outside)

        with self.assertRaises(WorkspaceError):
            self.store.get_project(item["id"])
        self.assertEqual(sentinel.read_text(encoding="utf-8"), '{"secret":"external"}')

    def test_project_record_junction_inserted_after_path_check_is_rejected(self):
        outside = Path(self.temp.name) / "outside-project-race-record"
        outside.mkdir()
        sentinel = outside / "keep.json"
        sentinel.write_text('{"secret":"external"}', encoding="utf-8")
        item = self.store.create_project("Projektdatei-Race")
        resolve_project_path = self.store._project_path

        def replace_record_after_check(project_id):
            record = resolve_project_path(project_id)
            record.unlink()
            self._create_junction(record, outside)
            return record

        with patch.object(self.store, "_project_path", replace_record_after_check):
            with self.assertRaises(WorkspaceError):
                self.store.get_project(item["id"])

        self.assertEqual(sentinel.read_text(encoding="utf-8"), '{"secret":"external"}')

    def test_artifact_symlink_does_not_modify_external_file(self):
        outside = Path(self.temp.name) / "outside.md"
        outside.write_text("geschützt", encoding="utf-8")
        link = self.store.artifacts_dir / "linked.md"
        try:
            link.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"Symlink unavailable on this Windows configuration: {exc}")

        saved = self.store.save_artifact("linked.md", "neuer Inhalt")
        self.assertNotEqual(saved, link)
        self.assertEqual(outside.read_text(encoding="utf-8"), "geschützt")

    def test_symlinked_workspace_directory_is_rejected(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        artifacts = self.store.artifacts_dir
        artifacts.rmdir()
        try:
            artifacts.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Symlink unavailable on this Windows configuration: {exc}")
        with self.assertRaises(WorkspaceError):
            WorkspaceStore(self.store.root)

    def test_invalid_project_id_is_rejected(self):
        with self.assertRaises(WorkspaceError):
            self.store.get_project("not-an-id")


if __name__ == "__main__":
    unittest.main()
