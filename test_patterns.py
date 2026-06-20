"""gentle pattern-noticing from the emotion signal - never a diagnosis."""

import tempfile
import unittest

from core import companion, datastore
from psychology import patterns


class TestPatterns(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_nothing_to_notice_when_quiet(self):
        self.assertIsNone(patterns.notice())
        for _ in range(2):
            companion.log_emotion("sadness", 0.6)
        self.assertIsNone(patterns.notice())          # below threshold

    def test_a_recurring_heavy_feeling_is_noticed(self):
        for _ in range(5):
            companion.log_emotion("fear", 0.6)
        note = patterns.notice()
        self.assertIsNotNone(note)
        self.assertEqual(note["emotion"], "fear")
        self.assertFalse(note["persistent"])
        self.assertIn("anxiety", note["line"])

    def test_persistent_leans_toward_real_help(self):
        for _ in range(9):
            companion.log_emotion("sadness", 0.7)
        note = patterns.notice()
        self.assertTrue(note["persistent"])
        self.assertIn("real person", note["line"])

    def test_joy_is_not_a_pattern_to_worry_about(self):
        for _ in range(8):
            companion.log_emotion("joy", 0.8)
        self.assertIsNone(patterns.notice())


if __name__ == "__main__":
    unittest.main()
