"""tests for codepath and the lesson session - the whole loop, headless."""

import os
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from core import datastore
from character import character_builder
from character.renderer import Character
from learning import codepath, progress_tracker
from learning.quiz_engine import LessonSession, wrap_text


def key(k, ch=""):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=ch)


class LessonTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name
        pack = character_builder.load_pack("gentle_guide")
        self.who = Character(character_builder.spec_from_pack(pack), pos=(300, 650), height=300)
        self.voice = pack["voice"]["phrases"]

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def session(self):
        return LessonSession("python", self.who, self.voice)

    def answer_current(self, s, right=True):
        # answer whatever exercise is on screen (works for any lesson shape)
        ex = s.ex
        if ex["type"] == "fill_blank":
            s.typed = str(ex["answer"]) if right else "definitely-wrong"
            s.handle(key(pygame.K_RETURN))
        else:
            idx = ex["answer_index"] if right else (ex["answer_index"] + 1) % len(ex["options"])
            s.handle(key(pygame.K_1 + idx))

    def solve_current_lesson(self, s):
        # walk every exercise of the current lesson until it advances
        start = s.lesson["id"]
        if s.state == "reading":
            s.handle(key(pygame.K_RETURN))
        guard = 0
        while s.lesson and s.lesson["id"] == start and s.state != "track_done" and guard < 60:
            if s.state == "question":
                self.answer_current(s)
            elif s.state == "done":
                s.handle(key(pygame.K_RETURN))
            guard += 1


class TestCodepath(LessonTest):

    def test_track_loads_in_teaching_order(self):
        lessons = codepath.load_track("python")
        self.assertEqual(len(lessons), 15)        # three clusters of five
        keys = [(l["cluster"], l["lesson"]) for l in lessons]
        self.assertEqual(keys, sorted(keys))       # ordered by cluster then lesson
        self.assertEqual(keys[0], (1, 1))

    def test_next_lesson_respects_the_log(self):
        first = codepath.next_lesson("python")
        self.assertEqual(first["lesson"], 1)
        progress_tracker.log_event("python", first["cluster"], first["id"], "lesson_done")
        self.assertEqual(codepath.next_lesson("python")["lesson"], 2)

    def test_finished_track_returns_none(self):
        for lesson in codepath.load_track("python"):
            progress_tracker.log_event("python", lesson["cluster"], lesson["id"], "lesson_done")
        self.assertIsNone(codepath.next_lesson("python"))

    def test_every_exercise_has_hints(self):
        for lesson in codepath.load_track("python"):
            for ex in codepath.lesson_exercises(lesson):
                self.assertTrue(ex["hints"], lesson["id"])


class TestSession(LessonTest):

    def test_starts_reading_the_first_lesson(self):
        s = self.session()
        self.assertEqual(s.state, "reading")
        self.assertEqual(s.lesson["lesson"], 1)

    def test_right_answer_celebrates_and_logs(self):
        s = self.session()
        s.handle(key(pygame.K_RETURN))                  # reading -> question
        self.answer_current(s, right=True)
        self.assertEqual(s.state, "done")
        self.assertEqual(s.character.target, __import__("character.renderer", fromlist=["EXPRESSIONS"]).EXPRESSIONS["celebrating"])
        rows = progress_tracker.read_learning_log()
        self.assertEqual(rows[-1]["correct"], "yes")

    def test_wrong_answer_stays_kind_and_lets_you_retry(self):
        s = self.session()
        s.handle(key(pygame.K_RETURN))
        self.answer_current(s, right=False)
        self.assertEqual(s.state, "question")            # still here, not failed out
        self.assertIn(s.feedback, self.voice["incorrect"])
        self.assertEqual(progress_tracker.read_learning_log()[-1]["correct"], "no")

    def test_a_miss_brings_both_voices(self):
        s = self.session()
        s.handle(key(pygame.K_RETURN))
        self.answer_current(s, right=False)
        self.assertIsNotNone(s.pair)
        teacher, friend = s.pair
        self.assertIn(teacher, self.voice["teacher"])
        self.assertIn(friend, self.voice["friend"])
        # a hint clears the two-voice moment
        s.handle(key(pygame.K_h, "h"))
        self.assertIsNone(s.pair)

    def test_hints_reveal_one_at_a_time_and_stop_at_three(self):
        s = self.session()
        s.handle(key(pygame.K_RETURN))
        for expected in (1, 2, 3, 3):
            s.handle(key(pygame.K_h, "h"))
            self.assertEqual(s.hints, expected)
        hint_rows = [r for r in progress_tracker.read_learning_log() if r["event"] == "hint"]
        self.assertEqual(len(hint_rows), 3)

    def test_a_missed_question_comes_back_next_session(self):
        # miss lesson one's quiz, then leave (as if quitting mid-session)
        s = self.session()
        s.handle(key(pygame.K_RETURN))
        self.answer_current(s, right=False)
        missed_id = s.lesson["id"]
        # a fresh session: the character brings the missed one back first
        s2 = self.session()
        self.assertTrue(s2.reviewing)
        self.assertEqual(s2.lesson["id"], missed_id)
        self.assertIn("missed this one before", s2.opening)
        # answering it right mends it and moves on
        s2.handle(key(pygame.K_RETURN))
        self.answer_current(s2, right=True)
        self.assertFalse(s2.reviewing)

    def test_finishing_advances_to_the_next_lesson(self):
        s = self.session()
        self.solve_current_lesson(s)                     # all of lesson 1's exercises
        self.assertEqual(s.lesson["lesson"], 2)
        self.assertEqual(s.state, "reading")

    def test_fill_blank_accepts_typed_answer_any_case(self):
        # lesson 3 is the fill_blank. finish 1 and 2 first.
        for lesson in codepath.load_track("python")[:2]:
            progress_tracker.log_event("python", lesson["cluster"], lesson["id"], "lesson_done")
        s = self.session()
        self.assertTrue(any(e["type"] == "fill_blank" for e in s.exercises))
        s.handle(key(pygame.K_RETURN))
        # answer the first fill_blank exercise, in the wrong case, and it still takes
        while s.ex["type"] != "fill_blank":
            self.answer_current(s, right=True)
            s.handle(key(pygame.K_RETURN))
        s.typed = str(s.ex["answer"]).swapcase()
        s.handle(key(pygame.K_RETURN))
        self.assertEqual(s.state, "done")

    def test_hesitation_is_noticed_once_and_only_once(self):
        s = self.session()
        s.handle(key(pygame.K_RETURN))
        s.shown_at -= 20                                  # pretend 20 quiet seconds
        s.update(0.016)
        self.assertIn(s.feedback, self.voice["hesitation"])
        first = s.feedback
        s.feedback = None
        s.update(0.016)
        self.assertIsNone(s.feedback)                     # not nagged twice
        self.assertTrue(first)

    def test_whole_track_draws_at_every_state(self):
        surface = pygame.Surface((1280, 720))
        s = self.session()
        while s.state != "track_done":
            s.draw(surface)
            if s.state == "reading":
                s.handle(key(pygame.K_RETURN))
            elif s.state == "question":
                self.answer_current(s, right=True)
            elif s.state == "done":
                s.draw(surface)
                s.handle(key(pygame.K_RETURN))
        s.draw(surface)                                   # the farewell panel
        self.assertIsNone(codepath.next_lesson("python"))


_RICH = {
    "track": "python", "cluster": 1, "lesson": 1, "id": "py-test-rich", "title": "Rich",
    "concept": "c", "explanation": "e", "code_example": "x = 1",
    "exercises": [
        {"type": "predict_output", "question": "q1", "options": ["a", "b"],
         "answer_index": 1, "hints": ["h1"]},
        {"type": "fill_blank", "question": "q2", "answer": "foo", "hints": ["h2"]},
        {"type": "predict_output", "question": "q3", "options": ["a", "b", "c"],
         "answer_index": 0, "hints": ["h3"]},
    ],
}

_OLD = {"track": "python", "cluster": 1, "lesson": 1, "id": "py-old", "title": "Old",
        "concept": "c", "explanation": "e", "code_example": "x = 1",
        "quiz": {"type": "predict_output", "question": "q", "options": ["a", "b"],
                 "answer_index": 0},
        "hints": ["a", "b", "c"]}


class TestExerciseNormalizing(unittest.TestCase):

    def test_old_lesson_becomes_one_exercise_with_its_hints(self):
        ex = codepath.lesson_exercises(_OLD)
        self.assertEqual(len(ex), 1)
        self.assertEqual(ex[0]["hints"], ["a", "b", "c"])

    def test_rich_lesson_keeps_its_exercises(self):
        ex = codepath.lesson_exercises(_RICH)
        self.assertEqual(len(ex), 3)
        self.assertEqual(ex[1]["type"], "fill_blank")


class TestMultiExercise(LessonTest):

    def setUp(self):
        super().setUp()
        self._next, self._review = codepath.next_lesson, codepath.review_lesson
        self._served = []
        def fake_next(track):
            # serve the rich lesson once, then the track is done
            self._served.append(1)
            return _RICH if len(self._served) == 1 else None
        codepath.next_lesson   = fake_next
        codepath.review_lesson = lambda t: None

    def tearDown(self):
        codepath.next_lesson, codepath.review_lesson = self._next, self._review
        super().tearDown()

    def test_walks_every_exercise_before_the_lesson_is_done(self):
        s = self.session()
        self.assertEqual(len(s.exercises), 3)
        s.handle(key(pygame.K_RETURN))               # reading -> first question
        # exercise 1: multiple choice, answer index 1
        s.handle(key(pygame.K_1 + 1))
        self.assertEqual(s.state, "done")
        s.handle(key(pygame.K_RETURN))               # -> exercise 2
        self.assertEqual(s.ex_i, 1)
        # exercise 2: fill blank
        s.typed = "foo"
        s.handle(key(pygame.K_RETURN))
        self.assertEqual(s.state, "done")
        s.handle(key(pygame.K_RETURN))               # -> exercise 3
        self.assertEqual(s.ex_i, 2)
        s.handle(key(pygame.K_1 + 0))                # last one, answer index 0
        self.assertEqual(s.state, "done")
        s.handle(key(pygame.K_RETURN))               # -> finishes the lesson
        self.assertEqual(s.state, "track_done")
        done = [r for r in progress_tracker.read_learning_log()
                if r.get("event") == "lesson_done" and r["lesson"] == "py-test-rich"]
        self.assertEqual(len(done), 1)               # the lesson completes exactly once


class TestWrap(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_wraps_and_keeps_newlines(self):
        font = pygame.font.Font(None, 24)
        lines = wrap_text(font, "one two three\nfour", 60)
        self.assertGreaterEqual(len(lines), 2)
        self.assertEqual(lines[-1], "four")


if __name__ == "__main__":
    unittest.main()
