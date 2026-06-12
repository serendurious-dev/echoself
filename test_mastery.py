"""tests for the don't-give-up layer: per-topic mastery, the one next step, and
the no-guilt welcome back. presence over pressure, made measurable."""

import datetime
import tempfile
import unittest

from core import datastore
from learning import mastery, progress_tracker, codepath


class _DataDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()


class TestMasteryReport(_DataDir):

    def test_a_fresh_start_reads_zero_with_a_first_step(self):
        r = mastery.report()
        self.assertEqual(r["overall"], 0.0)
        self.assertEqual(r["days_shown_up"], 0)
        self.assertEqual(r["next"]["kind"], "lesson")        # there's always a next step
        self.assertIn("day one", r["momentum"])

    def test_finishing_lessons_moves_the_topic_and_the_whole(self):
        # finish every lesson in cluster 1
        for lesson in codepath.load_track("python"):
            if lesson.get("cluster") == 1:
                progress_tracker.log_event("python", 1, lesson["id"], "lesson_done")
        r = mastery.report()
        c1 = next(c for c in r["clusters"] if c["cluster"] == 1)
        self.assertGreater(c1["mastery"], 0.0)
        self.assertGreater(r["overall"], 0.0)
        self.assertGreater(r["days_shown_up"], 0)

    def test_closer_than_it_feels_when_nearly_done_with_a_topic(self):
        # finish all of cluster 1 except its last lesson + extras left
        c1 = [l for l in codepath.load_track("python") if l.get("cluster") == 1]
        for lesson in c1[:-1]:
            progress_tracker.log_event("python", 1, lesson["id"], "lesson_done")
        r = mastery.report()
        # the next step should be that last cluster-1 lesson, and the line encourages
        self.assertEqual(r["next"]["cluster"], 1)
        self.assertTrue(r["next_line"])

    def test_welcome_back_only_after_a_real_gap_and_never_blames(self):
        old = datetime.datetime.now() - datetime.timedelta(days=6)
        progress_tracker.log_event("python", 1, "x", "lesson_done", when=old)
        line = mastery.welcome_back_line()
        self.assertIsNotNone(line)
        self.assertIn("no guilt", line)
        self.assertIn("6 days", line)

    def test_no_welcome_when_youve_been_around(self):
        progress_tracker.log_event("python", 1, "x", "lesson_done")   # today
        self.assertIsNone(mastery.welcome_back_line())


if __name__ == "__main__":
    unittest.main()
