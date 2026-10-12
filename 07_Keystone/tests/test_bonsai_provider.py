import json
import unittest
from unittest.mock import patch

from keystone_core.bonsai import BonsaiModelProvider
from keystone_core.contracts import ModelUnavailable


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.body).encode("utf-8")


class BonsaiProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = BonsaiModelProvider()

    @patch("keystone_core.bonsai.urllib.request.urlopen")
    def test_health(self, urlopen):
        urlopen.return_value = FakeResponse({"status": "ok"})
        self.assertEqual(self.provider.health()["provider"], "bonsai")
        self.assertEqual(urlopen.call_args.args[0].full_url, "http://127.0.0.1:8080/health")

    @patch("keystone_core.bonsai.urllib.request.urlopen")
    def test_list_models(self, urlopen):
        urlopen.return_value = FakeResponse(
            {"data": [{"id": "bonsai2-gguf/27B"}, {"id": "another"}]}
        )
        self.assertEqual(self.provider.list_models(), ["bonsai2-gguf/27B", "another"])

    @patch("keystone_core.bonsai.urllib.request.urlopen")
    def test_generate_returns_only_user_facing_content(self, urlopen):
        urlopen.return_value = FakeResponse(
            {"choices": [{"message": {"content": "Hallo!", "reasoning_content": "hidden"}}]}
        )
        self.assertEqual(self.provider.generate("Sag Hallo"), "Hallo!")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:8080/v1/chat/completions")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["messages"], [{"role": "user", "content": "Sag Hallo"}])
        self.assertFalse(payload["stream"])

    @patch("keystone_core.bonsai.urllib.request.urlopen")
    def test_empty_content_does_not_fall_back_to_reasoning(self, urlopen):
        urlopen.return_value = FakeResponse(
            {"choices": [{"message": {"content": "", "reasoning_content": "not user-facing"}}]}
        )
        with self.assertRaises(ModelUnavailable):
            self.provider.generate("Describe an image")

    @patch("keystone_core.bonsai.urllib.request.urlopen")
    def test_transport_error_is_mapped(self, urlopen):
        urlopen.side_effect = TimeoutError("timed out")
        with self.assertRaises(ModelUnavailable):
            self.provider.health()

    @patch("keystone_core.bonsai.urllib.request.urlopen")
    def test_malformed_model_listing_is_mapped(self, urlopen):
        urlopen.return_value = FakeResponse({"unexpected": []})
        with self.assertRaises(ModelUnavailable):
            self.provider.list_models()


if __name__ == "__main__":
    unittest.main()
