import os
import tempfile
import unittest
from pathlib import Path

from keystone_core.core import Keystone


class E2ESmokeTests(unittest.TestCase):
    @unittest.skipUnless(os.getenv("KEYSTONE_LIVE_E2E") == "1", "live WSL/Ollama test requires KEYSTONE_LIVE_E2E=1")
    def test_local_control_plane_to_hermes_to_ollama(self):
        with tempfile.TemporaryDirectory() as directory:
            core = Keystone(Path(directory), ollama_url=os.getenv("KEYSTONE_OLLAMA_URL", "http://127.0.0.1:11434"), model=os.getenv("KEYSTONE_OLLAMA_MODEL", "llama3.2:3b"))
            project = core.create_project("Gate 6 smoke")
            task = core.create_task(project.id, "local response")
            core.register_agent("SmokeAgent")
            result = core.run_task(task, "Reply with exactly: KEYSTONE E2E PASS")
            self.assertTrue(result)
            self.assertEqual(core.storage.list("events")[-1]["name"], "task.completed")
