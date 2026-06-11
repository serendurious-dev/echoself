"""tests for the rest of Layer 2: echo distance, dark days, mirror report, charts."""

import os
import datetime
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from core import datastore, session_manager, echo_distance, narrative_engine
from learning import progress_tracker


class Layer2Test(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()


class TestEchoDistance(Layer2Test):

    def test_no_data_sits_in_the_middle(self):
        d = echo_distance.compute()
        for axis in echo_distance.AXES:
            self.assertAlmostEqual(d[axis], 0.5, delta=0.001)

    def test_light_moods_close_the_emotional_gap(self):
        for _ in range(5):
            session_manager.log_mood("good", 9)
        self.assertLess(echo_distance.compute()["emotional"], 0.2)

    def test_heavy_moods_open_it(self):
        for _ in range(5):
            session_manager.log_mood("heavy", 2)
        self.assertGreater(echo_distance.compute()["emotional"], 0.7)

    def test_finishing_lessons_closes_learning(self):
        before = echo_distance.compute()["learning"]
        for lesson in __import__("learning.codepath", fromlist=["load_track"]).load_track("python"):
            progress_tracker.log_event("python", lesson["cluster"], lesson["id"], "lesson_done")
        self.assertLess(echo_distance.compute()["learning"], before)

    def test_distances_are_saved_with_the_mood_and_read_back(self):
        session_manager.log_mood("ok", 6, distances=echo_distance.compute())
        rows = echo_distance.history(30)
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]), {"date", *echo_distance.AXES})


class TestDarkDays(Layer2Test):

    def test_a_low_streak_triggers_it(self):
        base = datetime.datetime.now()
        for i in (3, 2, 1):
            session_manager.log_mood("heavy", 3, when=base - datetime.timedelta(days=i))
        self.assertTrue(narrative_engine.dark_days_active())

    def test_one_good_day_breaks_the_streak(self):
        base = datetime.datetime.now()
        session_manager.log_mood("heavy", 3, when=base - datetime.timedelta(days=2))
        session_manager.log_mood("heavy", 3, when=base - datetime.timedelta(days=1))
        session_manager.log_mood("lighter", 8, when=base)
        self.assertFalse(narrative_engine.dark_days_active())

    def test_quiet_log_is_not_dark(self):
        self.assertFalse(narrative_engine.dark_days_active())


class TestMirrorReport(Layer2Test):

    def setUp(self):
        super().setUp()
        self.profile = {"your_name": "Aria", "ideal_self": {"name": "the one who stayed"}}

    def test_empty_week_is_still_kind(self):
        report = narrative_engine.mirror_report(self.profile)
        self.assertIn("the one who stayed", report)
        self.assertIn("still here", report)

    def test_a_lived_week_names_the_days(self):
        for i in range(3):
            session_manager.log_mood("heavy", 3,
                                     when=datetime.datetime.now() - datetime.timedelta(days=i))
        report = narrative_engine.mirror_report(self.profile)
        self.assertIn("Aria", report)
        self.assertIn("3 days", report)


class TestCharts(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_radar_renders_to_a_surface(self):
        from visual import analytics_charts
        d = {a: 0.4 for a in echo_distance.AXES}
        surf = analytics_charts.radar_surface(d)
        self.assertIsInstance(surf, pygame.Surface)
        self.assertGreater(surf.get_width(), 50)

    def test_timeline_handles_empty_and_full(self):
        from visual import analytics_charts
        self.assertIsInstance(analytics_charts.timeline_surface([]), pygame.Surface)
        rows = [{"date": "2026-06-0%d" % i, **{a: 0.5 for a in echo_distance.AXES}}
                for i in range(1, 6)]
        self.assertIsInstance(analytics_charts.timeline_surface(rows), pygame.Surface)


if __name__ == "__main__":
    unittest.main()
