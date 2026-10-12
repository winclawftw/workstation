import unittest

from scripts.keystone_chat import MAX_HISTORY_MESSAGES, append_history_turn


class ChatHistoryTests(unittest.TestCase):
    def test_history_keeps_only_newest_sixteen_messages(self):
        history = []
        for number in range(10):
            history = append_history_turn(history, f"user {number}", f"assistant {number}")

        self.assertEqual(len(history), MAX_HISTORY_MESSAGES)
        self.assertEqual(history[0], {"role": "user", "content": "user 2"})
        self.assertEqual(history[-1], {"role": "assistant", "content": "assistant 9"})


if __name__ == "__main__":
    unittest.main()
