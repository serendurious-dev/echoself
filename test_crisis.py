"""crisis safety: the right lines for the region, deterministic and offline."""

import datetime
import tempfile
import unittest

from core import crisis, companion, datastore, settings, emotion


class TestCrisisResources(unittest.TestCase):

    def test_default_region_is_korea(self):
        self.assertTrue(any("109" in line for line in crisis.resources_for(None)))

    def test_a_known_region_swaps_the_local_line(self):
        lines = crisis.resources_for("US")
        self.assertTrue(any("988" in line for line in lines))
        self.assertFalse(any("109" in line for line in lines))

    def test_international_help_is_always_there(self):
        for region in (None, "US", "ZZ"):
            self.assertTrue(any("emergency number" in line
                                for line in crisis.resources_for(region)))

    def test_reply_keeps_the_care_and_carries_the_line(self):
        r = crisis.reply("US")
        self.assertIn("not a person who can keep you safe", r)
        self.assertIn("988", r)


class TestRegionPicker(unittest.TestCase):

    def test_names_known_regions(self):
        self.assertEqual(crisis.region_name("US"), "United States")
        self.assertEqual(crisis.region_name("kr"), "South Korea")
        self.assertEqual(crisis.region_name("ZZ"), "ZZ")     # unknown falls through

    def test_cycle_wraps_and_covers_everything(self):
        # walking next_region from KR visits every region and comes home
        seen, code = [], "KR"
        for _ in range(len(crisis.REGIONS)):
            seen.append(code)
            code = crisis.next_region(code)
        self.assertEqual(set(seen), set(crisis.REGIONS))
        self.assertEqual(code, "KR")                          # wrapped back

    def test_every_resource_region_is_in_the_cycle_and_named(self):
        for region in crisis.RESOURCES:
            self.assertIn(region, crisis.REGIONS, region)
            self.assertNotEqual(crisis.region_name(region), region)   # has a real name


class TestCrisisDetection(unittest.TestCase):
    # the gate itself - err toward catching, since a missed crisis is the worst outcome

    def test_catches_passive_and_indirect_phrasings(self):
        for s in ("i just want to disappear", "i wish i wasn't here anymore",
                  "i don't want to wake up tomorrow", "i can't keep living like this",
                  "no longer want to live", "ready to die honestly",
                  "everyone would be better off without me"):
            self.assertTrue(emotion.is_crisis(s), s)

    def test_normalises_spacing_and_smart_apostrophes(self):
        self.assertTrue(emotion.is_crisis("i want  to   die"))
        self.assertTrue(emotion.is_crisis("i don" + chr(0x2019) + "t want to be alive"))   # curly quote

    def test_does_not_fire_on_ordinary_heaviness(self):
        for s in ("i feel so sad and empty", "this week has been exhausting",
                  "i'm really stressed about work"):
            self.assertFalse(emotion.is_crisis(s), s)


class TestCrisisInCompanion(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_default_points_to_korea(self):
        r = companion.respond("I want to die")
        self.assertTrue(r["crisis"])
        self.assertIn("109", r["reply"])

    def test_region_setting_changes_the_lines(self):
        settings.set("region", "US")
        r = companion.respond("I want to die")
        self.assertTrue(r["crisis"])
        self.assertIn("988", r["reply"])
        self.assertNotIn("109", r["reply"])


class TestConcernTier(unittest.TestCase):
    # below crisis, above ordinary heaviness - adds care, never downgrades anything

    _NOTE = "carry this by yourself"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_detects_sinking_not_crisis_not_ordinary(self):
        self.assertTrue(crisis.is_concern("honestly i can't keep going like this"))
        self.assertTrue(crisis.is_concern("i feel like such a burden to everyone"))
        self.assertFalse(crisis.is_concern("i feel a bit sad today"))
        self.assertFalse(crisis.is_concern("i want to die"))     # crisis, handled first

    def test_respond_adds_the_soft_help_word(self):
        r = companion.respond("i can't keep going like this")
        self.assertFalse(r["crisis"])
        self.assertIn(self._NOTE, r["reply"])

    def test_crisis_still_wins_and_is_not_just_a_concern(self):
        r = companion.respond("i want to die, i can't keep going")
        self.assertTrue(r["crisis"])
        self.assertIn("109", r["reply"])
        self.assertNotIn(self._NOTE, r["reply"])      # the full crisis reply, not the soft note

    def test_ordinary_heaviness_gets_no_note(self):
        self.assertNotIn(self._NOTE, companion.respond("i feel so sad and empty")["reply"])

    def test_conversation_says_it_once(self):
        c = companion.Conversation(now=datetime.datetime(2026, 6, 13, 14, 0))
        c.open()
        r1 = c.say("i can't keep going like this")
        r2 = c.say("i can't keep doing this either")
        self.assertIn(self._NOTE, r1["reply"])
        self.assertNotIn(self._NOTE, r2["reply"])     # once a sitting, not nagging


if __name__ == "__main__":
    unittest.main()
