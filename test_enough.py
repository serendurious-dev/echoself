"""tests for the 'enough' judgment - effort measured against the day's capacity."""

import os
import datetime
import tempfile
import unittest

from core import datastore, session_manager, enough
from learning import progress_tracker


class EnoughTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name
        self.now = datetime.datetime.now()

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def effort(self, n):
        for i in range(n):
            progress_tracker.log_event("python", 1, f"l{i}", "quiz", correct="yes", when=self.now)


class TestCapacity(EnoughTest):

    def test_heavy_days_expect_little_light_days_expect_more(self):
        self.assertEqual(enough.capacity_expected(2), 0)
        self.assertLess(enough.capacity_expected(3), enough.capacity_expected(9))
        self.assertGreaterEqual(enough.capacity_expected(10), 3)


class TestVerdict(EnoughTest):

    def test_absent_day_is_kind_not_a_failure(self):
        v = enough.verdict()
        self.assertFalse(v["enough"])
        self.assertEqual(v["basis"], "absent")
        self.assertIn("ready", v["line"])

    def test_showing_up_on_a_heavy_day_is_enough(self):
        session_manager.log_mood("heavy", 2, when=self.now)   # low mood, no lessons
        v = enough.verdict()
        self.assertTrue(v["enough"])
        self.assertEqual(v["basis"], "showed_up")

    def test_meeting_the_days_capacity_is_enough(self):
        session_manager.log_mood("okay", 8, when=self.now)    # capacity ~2
        self.effort(2)
        v = enough.verdict()
        self.assertTrue(v["enough"])
        self.assertEqual(v["basis"], "capacity")

    def test_some_effort_short_of_capacity_still_counts(self):
        session_manager.log_mood("okay", 9, when=self.now)    # capacity ~3
        self.effort(1)
        v = enough.verdict()
        self.assertTrue(v["enough"])
        self.assertEqual(v["basis"], "effort")

    def test_a_light_day_with_nothing_done_is_not_yet_but_never_shaming(self):
        # high mood, showed up to log it, but did no work and didn't meet capacity
        session_manager.log_mood("bright", 9, when=self.now)
        v = enough.verdict()
        # capacity for mood 9 is ~3, effort 0 -> not_yet
        self.assertEqual(v["basis"], "not_yet")
        self.assertFalse(v["enough"])
        self.assertNotIn("fail", v["line"].lower())

    def test_effort_without_a_mood_log_still_registers(self):
        self.effort(2)                                        # did work, never logged mood
        v = enough.verdict()
        self.assertTrue(v["enough"])
        self.assertEqual(v["effort"], 2)


if __name__ == "__main__":
    unittest.main()
