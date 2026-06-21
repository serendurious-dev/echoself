"""the richer offline patterns she reads from the emotion rhythm (no words)."""

import datetime
import tempfile
import unittest

from core import portrait, companion, datastore


class TestPortraitPatterns(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def _log(self, emo, intensity, hour, day=16):
        # a fixed weekday date so weekend/weekday noise doesn't enter
        companion.log_emotion(emo, intensity,
                              when=datetime.datetime(2026, 6, day, hour, 0))

    def test_notices_the_heaviest_part_of_the_day(self):
        for _ in range(4):
            self._log("sadness", 0.8, 20)     # heavy evenings
        for _ in range(4):
            self._log("sadness", 0.3, 8)      # light mornings
        found = portrait.refresh_patterns()
        self.assertTrue(any("evenings tend to be the heaviest" in f for f in found), found)

    def test_notices_the_weight_easing(self):
        for _ in range(6):
            self._log("sadness", 0.8, 14)     # older, heavier
        for _ in range(6):
            self._log("sadness", 0.3, 14)     # newer, lighter
        found = portrait.refresh_patterns()
        self.assertTrue(any("easing" in f for f in found), found)

    def test_notices_the_bright_side(self):
        for _ in range(8):
            self._log("joy", 0.7, 12)
        found = portrait.refresh_patterns()
        self.assertTrue(any("good moments" in f for f in found), found)

    def test_quiet_log_finds_nothing(self):
        self._log("sadness", 0.5, 14)
        self.assertEqual(portrait.refresh_patterns(), [])


if __name__ == "__main__":
    unittest.main()
