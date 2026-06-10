"""tests for the character: spec loading, blinking, expressions, drawing."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from character.renderer import (Character, CharacterSpec, EXPRESSIONS,
                                hex_to_rgb, gentle_guide, PACK_DIR)

SIZE = (640, 480)


class TestSpec(unittest.TestCase):

    def test_hex_to_rgb(self):
        self.assertEqual(hex_to_rgb("#7FB5A8"), (127, 181, 168))
        self.assertEqual(hex_to_rgb("000000"), (0, 0, 0))

    def test_loads_the_gentle_guide_pack(self):
        spec = gentle_guide()
        self.assertEqual(spec.palette[0], (127, 181, 168))
        self.assertEqual(spec.symbol, "lantern")
        self.assertEqual(spec.form, "soft")

    def test_missing_pack_falls_back_to_defaults(self):
        spec = CharacterSpec.from_pack(os.path.join(PACK_DIR, "does_not_exist.json"))
        self.assertEqual(len(spec.palette), 3)
        self.assertEqual(spec.symbol, "circle")


class TestCharacter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode(SIZE)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.who = Character(gentle_guide(), pos=(320, 400), height=220)

    def ticks(self, seconds):
        for _ in range(int(seconds / 0.016) + 1):
            self.who.update(0.016)

    def test_update_and_draw_do_not_crash(self):
        surface = pygame.Surface(SIZE)
        self.ticks(0.5)
        self.who.draw(surface)

    def test_drawing_actually_emits_light(self):
        surface = pygame.Surface(SIZE)   # black
        self.who.draw(surface)
        # the additive composite must have brightened something
        self.assertGreater(pygame.transform.average_color(surface)[0:3], (0, 0, 0))

    def test_blink_happens_and_ends(self):
        self.who._next_blink = 0.0
        self.who.update(0.016)
        self.assertIsNotNone(self.who._blink_phase)   # mid-blink
        self.ticks(0.4)
        self.assertIsNone(self.who._blink_phase)      # eyes open again
        self.assertGreater(self.who._next_blink, 0.0)

    def test_expressions_ease_toward_target(self):
        self.who.set_expression("celebrating")
        before = self.who.expr["glow"]
        self.ticks(1.0)
        self.assertGreater(self.who.expr["glow"], before)
        self.assertAlmostEqual(self.who.expr["glow"],
                               EXPRESSIONS["celebrating"]["glow"], delta=0.1)

    def test_unknown_expression_is_an_error(self):
        with self.assertRaises(ValueError):
            self.who.set_expression("smug")

    def test_every_symbol_draws(self):
        surface = pygame.Surface(SIZE)
        for symbol in ("circle", "star", "spark", "lantern", "???"):
            self.who.spec.symbol = symbol
            self.who.draw(surface)

    def test_every_expression_draws(self):
        surface = pygame.Surface(SIZE)
        for name in EXPRESSIONS:
            self.who.set_expression(name)
            self.ticks(0.2)
            self.who.draw(surface)


if __name__ == "__main__":
    unittest.main()
