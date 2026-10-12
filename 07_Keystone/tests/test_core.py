import tempfile
import unittest
from pathlib import Path

from keystone_core.core import Keystone
from keystone_core.policy import PolicyEngine
from keystone_core.tools import ReadOnlyToolProvider


class CoreTests(unittest.TestCase):
    def test_policy_requires_approval_for_dangerous_actions(self):
        decision = PolicyEngine().evaluate("delete")
        self.assertFalse(decision.approved)
        self.assertTrue(decision.required)

    def test_read_only_tool_executes_and_audits(self):
        with tempfile.TemporaryDirectory() as directory:
            core = Keystone(Path(directory))
            result = core.execute_tool("get_current_directory")
            self.assertTrue(result)
            self.assertEqual(core.storage.list("events")[-1]["name"], "tool.executed")
            self.assertEqual(core.storage.list("audit")[-1]["action"], "tool.executed")

    def test_health_contracts_are_wired(self):
        provider = ReadOnlyToolProvider()
        self.assertEqual(provider.health()["status"], "ok")

    def test_task_path_checks_model_provider_before_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            core = Keystone(Path(directory))
            project = core.create_project("test")
            task = core.create_task(project.id, "run")
            calls = []

            class Provider:
                default_model = "local"
                def health(self): calls.append("health")
                def list_models(self): calls.append("list"); return ["local"]

            class Runtime:
                name = "fake"
                def run(self, prompt, *, model=None): calls.append(("run", model)); return "ok"

            core.model_provider = Provider()
            core.runtime = Runtime()
            self.assertEqual(core.run_task(task, "hello"), "ok")
            self.assertEqual(calls, ["health", "list", ("run", "local")])


if __name__ == "__main__":
    unittest.main()
