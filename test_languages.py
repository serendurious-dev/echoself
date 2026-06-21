"""tests for the language tracks: python deep, c / c++ / java as quiz intro
tracks, the active-track setting, and mastery per track."""

import tempfile
import unittest

from core import datastore, settings
from learning import codepath, mastery


class TestTracksLoad(unittest.TestCase):

    def test_all_four_languages_have_lessons(self):
        for track in ("python", "c", "cpp", "java"):
            lessons = codepath.load_track(track)
            self.assertTrue(lessons, f"{track} has no lessons")
            for lesson in lessons:
                # every lesson must be answerable: at least one exercise with hints,
                # whatever shape it's in (old single-quiz or the new exercise list)
                exercises = codepath.lesson_exercises(lesson)
                self.assertTrue(exercises, lesson["id"])
                for ex in exercises:
                    self.assertIn(ex["type"], ("mcq", "predict_output", "fill_blank"))
                    self.assertTrue(ex["hints"], lesson["id"])

    def test_quiz_answers_are_in_range(self):
        for track in ("c", "cpp", "java"):
            for lesson in codepath.load_track(track):
                for ex in codepath.lesson_exercises(lesson):
                    if ex["type"] in ("mcq", "predict_output"):
                        self.assertTrue(0 <= ex["answer_index"] < len(ex["options"]),
                                        f"{lesson['id']} bad answer_index")

    def test_dsa_course_loads_and_is_well_formed(self):
        lessons = codepath.load_track("dsa")
        self.assertEqual(len(lessons), 15)               # three clusters of five
        self.assertEqual([(l["cluster"], l["lesson"]) for l in lessons],
                         sorted((l["cluster"], l["lesson"]) for l in lessons))
        self.assertEqual(mastery.track_name("dsa"), "Data Structures")
        self.assertIn(("dsa", "Data Structures"), mastery.TRACKS)
        for lesson in lessons:
            exercises = codepath.lesson_exercises(lesson)
            self.assertTrue(exercises, lesson["id"])
            for ex in exercises:
                self.assertIn(ex["type"], ("mcq", "predict_output", "fill_blank"))
                self.assertTrue(ex["hints"], lesson["id"])
                if ex["type"] in ("mcq", "predict_output"):
                    self.assertTrue(0 <= ex["answer_index"] < len(ex["options"]),
                                    f"{lesson['id']} bad answer_index")

    def test_os_course_loads_and_is_well_formed(self):
        lessons = codepath.load_track("os")
        self.assertEqual(len(lessons), 5)
        self.assertEqual(mastery.track_name("os"), "How Computers Work")
        self.assertIn(("os", "How Computers Work"), mastery.TRACKS)
        for lesson in lessons:
            exercises = codepath.lesson_exercises(lesson)
            self.assertTrue(exercises, lesson["id"])
            for ex in exercises:
                self.assertIn(ex["type"], ("mcq", "predict_output", "fill_blank"))
                self.assertTrue(ex["hints"], lesson["id"])
                if ex["type"] in ("mcq", "predict_output"):
                    self.assertTrue(0 <= ex["answer_index"] < len(ex["options"]),
                                    f"{lesson['id']} bad answer_index")

    def test_python_stays_the_deep_one(self):
        self.assertGreaterEqual(len(codepath.load_track("python")), 15)
        self.assertTrue(codepath.load_extras("python"))            # has real coding challenges
        self.assertFalse(codepath.load_extras("c"))                # intro tracks are quiz-only


class TestActiveTrack(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_default_is_python_and_it_can_switch(self):
        self.assertEqual(mastery.active_track(), "python")
        settings.set("learning_track", "java")
        self.assertEqual(mastery.active_track(), "java")
        self.assertEqual(mastery.report()["track"], "java")        # report follows the setting
        self.assertEqual(mastery.report()["track_name"], "Java")

    def test_mastery_reads_each_track(self):
        for track, name in mastery.TRACKS:
            r = mastery.report(track)
            self.assertEqual(r["track"], track)
            self.assertGreaterEqual(r["clusters"][0]["total"], 5)  # an intro cluster's worth


if __name__ == "__main__":
    unittest.main()
