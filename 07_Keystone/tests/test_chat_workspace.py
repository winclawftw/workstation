import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import scripts.keystone_chat as keystone_chat
from keystone_core.workspace import MAX_PROJECT_RECORD_BYTES, WorkspaceStore


class HealthyProvider:
    name = "test"
    default_model = "test-model"

    def __init__(self, *args, **kwargs):
        pass

    def health(self):
        return {"status": "ok"}


class ChatWorkspaceTests(unittest.TestCase):
    def test_project_list_reports_corrupt_and_oversized_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "checkout"
            store = WorkspaceStore(root / "data")
            project = store.create_project("Gültiges Projekt")
            (store.projects_dir / "corrupt.json").write_text(
                '{"id":', encoding="utf-8"
            )
            (store.projects_dir / "oversized.json").write_bytes(
                b" " * (MAX_PROJECT_RECORD_BYTES + 1)
            )

            output = io.StringIO()
            with (
                patch.object(keystone_chat, "ROOT", root),
                patch.object(keystone_chat, "BonsaiModelProvider", HealthyProvider),
                patch("builtins.input", side_effect=["/project list", "/exit"]),
                redirect_stdout(output),
            ):
                self.assertEqual(keystone_chat.main(), 0)

            text = output.getvalue()
            self.assertIn(project["name"], text)
            self.assertIn("Warning: skipped project record: corrupt.json", text)
            self.assertIn("Warning: skipped project record: oversized.json", text)
            self.assertNotIn("No projects yet", text)


if __name__ == "__main__":
    unittest.main()
