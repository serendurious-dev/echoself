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

    def test_every_pack_has_both_voices(self):
        # the AlterEgo two-voice concept: a teacher register and a friend register
        for pack in character_builder.all_packs():
            for slot in ("teacher", "friend"):
                lines = pack["voice"]["phrases"].get(slot)
                self.assertTrue(lines, f"{pack['id']} is missing the '{slot}' voice")


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

    def test_palette_override_colors_the_light(self):
        pack = character_builder.load_pack("gentle_guide")
        spec = character_builder.spec_from_pack(pack, palette=["#C77B8B", "#F0D8DC", "#5A3A44"])
        self.assertEqual(spec.palette[0], (199, 123, 139))   # the chosen light, not the preset's

    def test_spec_from_profile_and_fallback(self):
        profile = {"character": {"pack": "playful_rival", "hair_style": "spiky",
                                 "skin": "#D9A878", "palette": ["#7AA86A", "#DCE8C8", "#3E5238"]}}
        spec = character_builder.spec_from_profile(profile)
        self.assertEqual(spec.symbol, "star")
        self.assertEqual(spec.palette[0], (122, 168, 106))   # profile palette applied
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


class TestMakeYourself(unittest.TestCase):
    # the full "make your own" path: every knob the renderer draws is reachable,
    # saved, and rebuilt - and a custom look carries a separately chosen voice.

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((320, 240))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_the_full_swatch_sets_exist(self):
        cb = character_builder
        for swatches in (cb.FORMS, cb.HAIR_COLORS, cb.EYE_COLORS, cb.OUTFITS, cb.SYMBOLS):
            self.assertTrue(swatches)
        self.assertIn("circle", cb.SYMBOLS)

    def test_every_knob_lays_over_the_base(self):
        pack = character_builder.load_pack("gentle_guide")
        spec = character_builder.spec_from_pack(
            pack, build="male", form="broad", hair_style="spiky",
            hair_color="#2B2622", skin="#6B4A35", eye_color="#3E6E8A",
            outfit=["#9B8AC4", "#5A4E78"],
            palette=["#C77B8B", "#F0D8DC", "#5A3A44"], symbol="star")
        self.assertEqual(spec.gender, "male")
        self.assertEqual(spec.form, "broad")
        self.assertEqual(spec.hair_style, "spiky")
        self.assertEqual(spec.hair_color, (43, 38, 34))
        self.assertEqual(spec.skin, (107, 74, 53))
        self.assertEqual(spec.eye_color, (62, 110, 138))
        self.assertEqual(spec.outfit[0], (155, 138, 196))
        self.assertEqual(spec.palette[0], (199, 123, 139))
        self.assertEqual(spec.symbol, "star")

    def test_a_custom_profile_rebuilds_and_renders(self):
        profile = {"character": {
            "pack": "custom", "voice": "strict_mentor", "build": "male",
            "form": "slender", "hair_style": "short", "hair_color": "#E8D5A8",
            "skin": "#A8714A", "eye_color": "#5B8A80",
            "outfit": ["#7AA86A", "#4E6E48"],
            "palette": ["#9B8AC4", "#D8CCE8", "#4A4458"], "symbol": "spark"}}
        spec = character_builder.spec_from_profile(profile)
        self.assertEqual(spec.gender, "male")
        self.assertEqual(spec.hair_style, "short")
        self.assertEqual(spec.eye_color, (91, 138, 128))
        self.assertEqual(spec.palette[0], (155, 138, 196))
        self.assertEqual(spec.symbol, "spark")
        # the look is custom, the voice is whoever they picked
        self.assertEqual(character_builder.voice_from_profile(profile),
                         character_builder.load_pack("strict_mentor")["voice"]["phrases"])
        # and it actually draws
        surface = pygame.Surface((320, 240))
        who = Character(spec, pos=(160, 220), height=160)
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
