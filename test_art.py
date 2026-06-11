"""tests for the layered-art pipeline: loading, animation, blink, mouth, fallback.

generates a placeholder pack into a tempdir so no binary art lives in the repo.
"""

import os
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from character import art_pack, character_builder
from character.renderer import Character, CharacterSpec
from tools.make_placeholder_art import write_placeholder_pack


class ArtTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((640, 480))
        cls._tmp = tempfile.TemporaryDirectory()
        cls.pack = os.path.join(cls._tmp.name, "demo")
        write_placeholder_pack(cls.pack)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()
        pygame.quit()

    def make(self):
        return art_pack.ArtCharacter(CharacterSpec(), pos=(320, 460), height=300,
                                     art_dir=self.pack)

    def test_loads_every_layer(self):
        who = self.make()
        self.assertEqual(len(who.layers), 9)
        self.assertTrue(who._has_closed)
        self.assertEqual(who._mouths, {"neutral", "happy", "open"})

    def test_interface_matches_the_procedural_character(self):
        who = self.make()
        for attr in ("set_expression", "update", "draw", "pos", "h", "spec"):
            self.assertTrue(hasattr(who, attr))

    def test_update_and_draw_do_not_crash(self):
        who = self.make()
        surface = pygame.Surface((640, 480))
        for _ in range(40):
            who.update(0.016)
        who.draw(surface)

    def test_blink_selects_the_closed_eyes(self):
        who = self.make()
        who._blink_phase = None
        self.assertFalse(who._blinking())
        who._blink_phase = 0.5
        self.assertTrue(who._blinking())
        closed = next(l for l, _ in who.layers if l.get("eyes") == "closed")
        open_  = next(l for l, _ in who.layers if l.get("eyes") == "open")
        self.assertTrue(who._visible(closed, who._mouth_for()))
        self.assertFalse(who._visible(open_, who._mouth_for()))

    def test_expression_picks_the_mouth(self):
        who = self.make()
        who.set_expression("celebrating")
        self.assertEqual(who._mouth_for(), "open")
        who.set_expression("happy")
        self.assertEqual(who._mouth_for(), "happy")
        who.set_expression("thinking")
        self.assertEqual(who._mouth_for(), "neutral")

    def test_unknown_expression_still_rejected(self):
        who = self.make()
        with self.assertRaises(ValueError):
            who.set_expression("smug")


class TestCodelPack(unittest.TestCase):
    # the real CC-BY pack that ships with the repo, a whole-sprite "pose" pack

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((640, 480))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_gentle_guide_renders_as_the_art_character(self):
        spec = character_builder.spec_from_pack(character_builder.load_pack("gentle_guide"))
        self.assertEqual(spec.art, "codel")
        who = character_builder.make_character(spec, height=300)
        self.assertIsInstance(who, art_pack.ArtCharacter)

    def test_each_expression_picks_its_own_sprite(self):
        spec = character_builder.spec_from_pack(character_builder.load_pack("gentle_guide"))
        who  = character_builder.make_character(spec, height=300)
        seen = {}
        for expr in ("neutral", "happy", "thinking", "drift"):
            who.set_expression(expr)
            seen[expr] = who._chosen_pose()["image"]
        self.assertEqual(len({tuple(seen.values())}), 1)   # all keys present
        self.assertEqual(len(set(seen.values())), 4)        # and all four differ

    def test_unknown_expression_falls_back_to_the_default_pose(self):
        spec = character_builder.spec_from_pack(character_builder.load_pack("gentle_guide"))
        who  = character_builder.make_character(spec, height=300)
        who.expr_name = "patient"
        self.assertEqual(who._chosen_pose()["image"], "patient.png")
        who.expr_name = "neutral"
        self.assertEqual(who._chosen_pose()["pose"], "default")

    def test_it_draws(self):
        spec = character_builder.spec_from_pack(character_builder.load_pack("gentle_guide"))
        who  = character_builder.make_character(spec, pos=(320, 460), height=300)
        surface = pygame.Surface((640, 480))
        who.set_expression("happy")
        who.update(0.1)
        who.draw(surface)


class FactoryTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((640, 480))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_no_art_gives_the_procedural_figure(self):
        who = character_builder.make_character(CharacterSpec(art=None))
        self.assertIsInstance(who, Character)

    def test_missing_pack_falls_back(self):
        who = character_builder.make_character(CharacterSpec(art="does_not_exist"))
        self.assertIsInstance(who, Character)

    def test_real_pack_gives_the_art_figure(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_placeholder_pack(os.path.join(tmp, "demo"))
            old, art_pack.ART_DIR = art_pack.ART_DIR, tmp
            try:
                who = character_builder.make_character(CharacterSpec(art="demo"))
                self.assertIsInstance(who, art_pack.ArtCharacter)
            finally:
                art_pack.ART_DIR = old


if __name__ == "__main__":
    unittest.main()
