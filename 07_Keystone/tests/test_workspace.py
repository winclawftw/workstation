import json
import tempfile
import unittest
from pathlib import Path
from keystone_core.workspace import WorkspaceError, WorkspaceStore


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = WorkspaceStore(Path(self.temp.name) / "data")

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
