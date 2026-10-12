import unittest

from keystone_core.models import ModelProvider
from keystone_core.runtime import AgentRuntime
from keystone_core.tools import ToolProvider


class ContractShapeTests(unittest.TestCase):
    def test_core_contracts_exist_as_runtime_checkable_protocols(self):
        self.assertTrue(hasattr(AgentRuntime, "run"))
        self.assertTrue(hasattr(ModelProvider, "generate"))
        self.assertTrue(hasattr(ToolProvider, "execute"))


if __name__ == "__main__":
    unittest.main()
