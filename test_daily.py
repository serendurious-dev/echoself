"""tests for the daily check-in: she reads the day's mood from the conversation
instead of a form, and logs the number underneath so the brain still gets it."""

import datetime
import tempfile
import unittest

from core import daily, companion, session_manager, datastore


def _conv_saying(lines):
    conv = companion.Conversation(now=datetime.datetime(2026, 6, 13, 19, 0))
    conv.open()
    for line in lines:
        conv.say(line)
    return conv


class TestMoodFromConversation(unittest.TestCase):

    def test_a_heavy_talk_reads_low(self):
        conv = _conv_saying(["i feel so empty and sad", "still really low today"])
        word, score = daily.mood_from_conversation(conv)
        self.assertEqual(word, "low")
        self.assertLessEqual(score, 4)

    def test_a_good_talk_reads_high(self):
        conv = _conv_saying(["today was wonderful, I feel proud and grateful"])
        word, score = daily.mood_from_conversation(conv)
        self.assertEqual(word, "good")
        self.assertGreaterEqual(score, 8)

    def test_saying_nothing_logs_nothing(self):
        conv = companion.Conversation(now=datetime.datetime(2026, 6, 13, 19, 0))
        conv.open()                       # she opened, you never answered
        self.assertEqual(daily.mood_from_conversation(conv), (None, None))


class TestLogCheckin(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_a_check_in_writes_the_days_mood_row(self):
        conv = _conv_saying(["honestly I'm so anxious about everything"])
        result = daily.log_checkin(conv, {})
        self.assertIsNotNone(result)
        rows = session_manager.read_echo_log()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["mood_word"], "anxious")

    def test_an_empty_check_in_writes_nothing(self):
        conv = companion.Conversation(now=datetime.datetime(2026, 6, 13, 19, 0))
        conv.open()
        self.assertIsNone(daily.log_checkin(conv, {}))
        self.assertEqual(session_manager.read_echo_log(), [])


if __name__ == "__main__":
    unittest.main()
