"""tests for session zero's plumbing: the packs, the specs, the profile."""

import os
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from core import datastore
from character import character_builder
from character.renderer import Character

PHRASE_SLOTS = ["greeting", "correct", "incorrect", "hesitation", "encouragement", "farewell"]


class TestPacks(unittest.TestCase):
    # every preset must be complete - a missing phrase slot would surface as a
    # crash mid-lesson, which is the worst possible moment

    def test_all_five_packs_load(self):
        packs = character_builder.all_packs()
        self.assertEqual(len(packs), 5)
        self.assertEqual([p["id"] for p in packs], character_builder.PACK_IDS)

    def test_every_pack_has_every_phrase_slot(self):
        for pack in character_builder.all_packs():
            for slot in PHRASE_SLOTS:
                lines = pack["voice"]["phrases"].get(slot)
                self.assertTrue(lines, f"{pack['id']} is missing '{slot}'")
                for line in lines:
                    self.assertTrue(line.strip(), f"{pack['id']} has an empty '{slot}' line")

    def test_every_pack_has_a_complete_visual_block(self):
        for pack in character_builder.all_packs():
            v = pack["visual"]
            for field in ("palette", "skin", "hair", "eyes", "outfit", "form", "symbol"):
                self.assertIn(field, v, f"{pack['id']} visual is missing '{field}'")

    def test_the_five_voices_are_actually_different(self):
        greetings = [p["voice"]["phrases"]["greeting"][0]
                     for p in character_builder.all_packs()]
        self.assertEqual(len(set(greetings)), 5)


class TestSpecs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((320, 240))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_overrides_lay_over_the_preset(self):
        pack = character_builder.load_pack("strict_mentor")
        spec = character_builder.spec_from_pack(pack, hair_style="long", skin="#6B4A35")
        self.assertEqual(spec.hair_style, "long")
        self.assertEqual(spec.skin, (107, 74, 53))
        self.assertEqual(spec.form, "slender")          # the preset's own field survives

    def test_spec_from_profile_and_fallback(self):
        profile = {"character": {"pack": "playful_rival", "hair_style": "spiky",
                                 "skin": "#D9A878"}}
        spec = character_builder.spec_from_profile(profile)
        self.assertEqual(spec.symbol, "star")
        # garbage in, gentle guide out - never a crash
        self.assertEqual(character_builder.spec_from_profile(None).symbol, "lantern")
        self.assertEqual(character_builder.spec_from_profile({"character": {"pack": "gone"}}).symbol,
                         "lantern")

    def test_voice_from_profile_falls_back_too(self):
        voice = character_builder.voice_from_profile({"character": {"pack": "quiet_empath"}})
        self.assertEqual(voice["correct"][0], "There it is.")
        self.assertIn("greeting", character_builder.voice_from_profile(None))

    def test_every_preset_renders(self):
        surface = pygame.Surface((320, 240))
        for pack in character_builder.all_packs():
            who = Character(character_builder.spec_from_pack(pack), pos=(160, 220), height=160)
            who.update(0.1)
            who.draw(surface)


class TestWorldsUseTheProfile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((320, 240))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_default_worlds_pick_up_the_chosen_character(self):
        from core import session_manager
        from visual.worlds import default_worlds
        with tempfile.TemporaryDirectory() as tmp:
            old, datastore.DATA_DIR = datastore.DATA_DIR, tmp
            try:
                session_manager.save_profile(
                    {"character": {"pack": "strict_mentor", "hair_style": "spiky",
                                   "skin": "#E8C9A8"}})
                worlds = default_worlds((320, 240))
                self.assertEqual(worlds["ambient"].character.spec.symbol, "spark")
            finally:
                datastore.DATA_DIR = old


if __name__ == "__main__":
    unittest.main()
