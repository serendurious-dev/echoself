"""tests for the world manager: switching, fading, the drift toggle."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")   # headless, no window
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from visual.worlds import WorldManager, FADE_SECONDS

SIZE = (320, 180)


def settle(manager, seconds=FADE_SECONDS * 2):
    # tick the manager well past a full fade
    steps = int(seconds / 0.016) + 1
    for _ in range(steps):
        manager.update(0.016)


class TestWorldManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode(SIZE)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.m = WorldManager(SIZE)

    def test_starts_in_ambient(self):
        self.assertEqual(self.m.current.name, "ambient")
        self.assertEqual(self.m.fade, 0.0)

    def test_switch_lands_after_the_fade(self):
        self.m.switch("learning")
        # mid-fade we are still in the old world, going dark
        self.m.update(0.016)
        self.assertEqual(self.m.current.name, "ambient")
        self.assertGreater(self.m.fade, 0.0)
        settle(self.m)
        self.assertEqual(self.m.current.name, "learning")
        self.assertEqual(self.m.fade, 0.0)

    def test_switch_to_current_world_does_nothing(self):
        self.m.switch("ambient")
        self.m.update(0.016)
        self.assertEqual(self.m.fade, 0.0)

    def test_retargeting_mid_fade_does_not_strand_you(self):
        self.m.switch("learning")
        self.m.update(0.016)
        self.m.switch("drift")   # changed my mind mid-fade
        settle(self.m)
        self.assertEqual(self.m.current.name, "drift")
        self.assertEqual(self.m.fade, 0.0)

    def test_drift_toggle_remembers_where_you_were(self):
        self.m.switch("learning")
        settle(self.m)
        self.m.toggle_drift()
        settle(self.m)
        self.assertEqual(self.m.current.name, "drift")
        self.m.toggle_drift()
        settle(self.m)
        self.assertEqual(self.m.current.name, "learning")

    def test_drift_from_start_returns_to_ambient(self):
        self.m.toggle_drift()
        settle(self.m)
        self.m.toggle_drift()
        settle(self.m)
        self.assertEqual(self.m.current.name, "ambient")

    def test_every_world_draws_without_crashing(self):
        surface = pygame.Surface(SIZE)
        for name in ("ambient", "learning", "drift"):
            self.m.switch(name)
            settle(self.m)
            self.m.draw(surface)

    def test_draw_during_fade_applies_the_veil(self):
        surface = pygame.Surface(SIZE)
        self.m.switch("learning")
        self.m.update(0.016)
        self.m.draw(surface)   # should not crash with the veil on top


if __name__ == "__main__":
    unittest.main()
