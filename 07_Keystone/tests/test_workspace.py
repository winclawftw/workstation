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

    def test_artifact_is_written_and_linked(self):
        item = self.store.create_project("Konzept")
        path = self.store.save_artifact("konzept.md", "# Entwurf\nText", item["id"])
        self.assertEqual(path.parent, self.store.artifacts_dir)
        self.assertIn("# Entwurf", path.read_text(encoding="utf-8"))
        self.assertEqual(self.store.get_project(item["id"])["artifacts"][0]["filename"], "konzept.md")

    def test_invalid_project_id_is_rejected(self):
        with self.assertRaises(WorkspaceError):
            self.store.get_project("not-an-id")


if __name__ == "__main__":
    unittest.main()
