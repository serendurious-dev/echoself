"""tests for the data layer: profile, mood log, learning log, first run."""

import os
import datetime
import tempfile
import unittest

from core import datastore, session_manager
from learning import progress_tracker


class DataTest(unittest.TestCase):
    # every test gets a fresh fake data/ dir, the real one is never touched

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()


class TestFirstRun(DataTest):

    def test_no_profile_means_none(self):
        self.assertIsNone(session_manager.load_profile())

    def test_empty_logs_read_as_empty_lists(self):
        self.assertEqual(session_manager.read_echo_log(), [])
        self.assertEqual(progress_tracker.read_learning_log(), [])
        self.assertEqual(progress_tracker.completed_lessons("python"), set())
        self.assertIsNone(progress_tracker.quiz_accuracy("python"))


class TestProfile(DataTest):

    def test_roundtrip(self):
        profile = {"ideal_self": {"name": "Aria", "values": ["honesty", "calm"]},
                   "shadow_self": {"name": "the tired one"}}
        session_manager.save_profile(profile)
        self.assertEqual(session_manager.load_profile(), profile)

    def test_unicode_survives(self):
        session_manager.save_profile({"name": "프로디타", "word": "괜찮아"})
        self.assertEqual(session_manager.load_profile()["word"], "괜찮아")

    def test_atomic_write_leaves_no_temp_files(self):
        session_manager.save_profile({"a": 1})
        session_manager.save_profile({"a": 2})
        leftovers = [f for f in os.listdir(self._tmp.name) if f.startswith(".tmp_")]
        self.assertEqual(leftovers, [])


class TestMoodLog(DataTest):

    def test_append_and_read(self):
        session_manager.log_mood("heavy", 3)
        session_manager.log_mood("lighter", 6)
        rows = session_manager.read_echo_log()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["mood_word"], "heavy")
        self.assertEqual(rows[1]["mood_score"], "6")

    def test_header_is_written_exactly_once(self):
        session_manager.log_mood("a", 5)
        session_manager.log_mood("b", 5)
        with open(datastore.data_path(session_manager.ECHO_LOG), encoding="utf-8") as f:
            first_field = session_manager.ECHO_FIELDS[0]
            headers = [line for line in f if line.startswith(first_field + ",")]
        self.assertEqual(len(headers), 1)

    def test_recent_entries_filters_by_date(self):
        old = datetime.datetime.now() - datetime.timedelta(days=40)
        session_manager.log_mood("long ago", 4, when=old)
        session_manager.log_mood("today", 7)
        recent = session_manager.recent_entries(30)
        self.assertEqual([r["mood_word"] for r in recent], ["today"])

    def test_distances_can_ride_along(self):
        session_manager.log_mood("ok", 5, distances={"mental": 0.4, "learning": 0.8})
        row = session_manager.read_echo_log()[0]
        self.assertEqual(row["mental"], "0.4")
        self.assertEqual(row["behavioral"], "")


class TestLearningLog(DataTest):

    def test_completed_lessons(self):
        progress_tracker.log_event("python", 1, "py-c1-l1", "lesson_done")
        progress_tracker.log_event("python", 1, "py-c1-l2", "quiz", correct="yes")
        done = progress_tracker.completed_lessons("python")
        self.assertEqual(done, {("1", "py-c1-l1")})

    def test_quiz_accuracy(self):
        for correct in ("yes", "yes", "no", "yes"):
            progress_tracker.log_event("python", 1, "py-c1-l1", "quiz", correct=correct)
        self.assertAlmostEqual(progress_tracker.quiz_accuracy("python"), 0.75)

    def test_missed_questions_forgives_a_later_success(self):
        progress_tracker.log_event("python", 1, "py-c1-l1", "quiz", correct="no")
        progress_tracker.log_event("python", 1, "py-c1-l2", "quiz", correct="no")
        progress_tracker.log_event("python", 1, "py-c1-l1", "quiz", correct="yes")
        missed = progress_tracker.missed_questions("python")
        self.assertEqual(missed, {("1", "py-c1-l2")})

    def test_tracks_do_not_leak_into_each_other(self):
        progress_tracker.log_event("python", 1, "a", "lesson_done")
        progress_tracker.log_event("c", 1, "a", "lesson_done")
        self.assertEqual(len(progress_tracker.completed_lessons("python")), 1)


if __name__ == "__main__":
    unittest.main()
