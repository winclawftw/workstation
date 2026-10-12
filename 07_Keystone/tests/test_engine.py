import unittest

from keystone_core.contracts import ModelUnavailable
from keystone_core.engine import KeystoneEngine


class MessageProvider:
    name = "mock"
    default_model = "mock-model"

    def __init__(self, answer="Antwort"):
        self.answer = answer
        self.messages = None

    def capabilities(self):
        return {"generate", "generate_messages"}

    def health(self):
        return {"status": "ok"}

    def list_models(self):
        return [self.default_model]

    def generate(self, prompt, *, model=None):
        return self.answer

    def generate_messages(self, messages, *, model=None):
        self.messages = messages
        return self.answer


class LegacyProvider:
    """ModelProvider-compatible provider with the original generate contract."""

    name = "legacy"
    default_model = "legacy-model"

    def capabilities(self):
        return {"generate"}

    def health(self):
        return {"status": "ok"}

    def list_models(self):
        return [self.default_model]

    def generate(self, prompt, *, model=None):
        return f"legacy:{prompt}"


class EngineTests(unittest.TestCase):
    def test_system_history_and_current_message_reach_message_provider(self):
        provider = MessageProvider()
        engine = KeystoneEngine(provider)
        reply = engine.respond(
            "Nächster Schritt?",
            history=[
                {"role": "user", "content": "Wir planen ein Konzept."},
                {"role": "assistant", "content": "Welche Zielgruppe?"},
                {"role": "system", "content": "Unerlaubte Historienrolle"},
                {"role": "user", "content": "Familien."},
            ],
            system_prompt="Bleibe pragmatisch.",
        )
        self.assertEqual(
            provider.messages,
            [
                {"role": "system", "content": "Bleibe pragmatisch."},
                {"role": "user", "content": "Wir planen ein Konzept."},
                {"role": "assistant", "content": "Welche Zielgruppe?"},
                {"role": "user", "content": "Familien."},
                {"role": "user", "content": "Nächster Schritt?"},
            ],
        )
        self.assertEqual(reply.text, "Antwort")

    def test_existing_generate_only_provider_contract_still_works(self):
        reply = KeystoneEngine(LegacyProvider()).respond("Weiterarbeiten")
        self.assertEqual(reply.text, "legacy:Weiterarbeiten")
        self.assertEqual(reply.provider, "legacy")

    def test_empty_model_response_is_not_success(self):
        with self.assertRaises(ModelUnavailable):
            KeystoneEngine(MessageProvider("  ")).respond("Weiterarbeiten")


if __name__ == "__main__":
    unittest.main()
