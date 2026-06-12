"""tests for the psychology depth: the new emotions, the sourced frameworks, and
the opt-in technique flow - she validates, offers a tool as a question, and only
walks it on a yes. crisis still overrides everything, including a pending offer."""

import datetime
import unittest

from core import emotion, companion
from psychology import frameworks


class TestNewEmotions(unittest.TestCase):

    def test_reads_the_feelings_the_first_six_missed(self):
        cases = {
            "I'm so burnt out, there's just too much to do": "overwhelm",
            "it was my fault, I should have done better": "guilt",
            "I miss them so much, I've been grieving for weeks": "grief",
            "I just feel nothing, nothing matters anymore": "numbness",
        }
        for text, expected in cases.items():
            self.assertEqual(emotion.detect(text)[0], expected, text)

    def test_the_original_six_still_read_the_same(self):
        # adding emotions must not shift the ones that already worked
        self.assertEqual(emotion.detect("I'm so anxious and overwhelmed about tomorrow")[0], "fear")
        self.assertEqual(emotion.detect("I'm such a failure, I'm not good enough")[0], "shame")
        self.assertEqual(emotion.detect("today was wonderful, I feel hopeful and proud")[0], "joy")

    def test_affirmation_reads_a_yes(self):
        for yes in ["yes", "okay", "sure", "yes please", "go ahead"]:
            self.assertTrue(emotion.is_affirmation(yes), yes)
        for no in ["no", "not really", "no thanks", "i'd rather not"]:
            self.assertFalse(emotion.is_affirmation(no), no)


class TestFrameworks(unittest.TestCase):

    def test_every_framework_is_complete_and_sourced(self):
        self.assertTrue(frameworks.FRAMEWORKS)
        for key, fw in frameworks.FRAMEWORKS.items():
            for field in ("name", "for", "source", "offer", "walk"):
                self.assertTrue(fw.get(field), f"{key} missing {field}")
            self.assertTrue(fw["offer"].strip().endswith("."))   # the offer is a gentle line

    def test_referenced_techniques_all_exist(self):
        # every emotion that names a technique must point at a real framework
        for emo, bank in companion.RESPONSES.items():
            tech = bank.get("technique")
            if tech:
                self.assertIsNotNone(frameworks.get(tech), f"{emo} -> missing {tech}")


class TestTechniqueFlow(unittest.TestCase):

    def _conv(self):
        return companion.Conversation(now=datetime.datetime(2026, 6, 13, 14, 0))

    def test_she_offers_a_tool_after_listening_then_walks_it_on_yes(self):
        conv = self._conv()
        conv.open()
        conv.say("I'm so anxious and scared about tomorrow")      # turn 1: validate
        r2 = conv.say("still really anxious, my chest is tight")  # turn 2: stayed -> offer
        self.assertIn(frameworks.offer_line("grounding_54321"), r2["reply"])
        r3 = conv.say("yes")                                      # the walk
        self.assertEqual(r3["reply"], frameworks.walk("grounding_54321"))
        self.assertIn("five things you can see", r3["reply"])

    def test_a_no_drops_it_without_pushing(self):
        conv = self._conv()
        conv.open()
        conv.say("I'm so anxious and scared")
        conv.say("still anxious")                                 # offer made here
        r = conv.say("no, I just want to vent")
        self.assertNotIn("five things you can see", r["reply"])   # not walked
        self.assertIsNone(conv._offered)                          # and not left hanging

    def test_a_tool_is_offered_at_most_once_a_sitting(self):
        conv = self._conv()
        conv.open()
        conv.say("I'm anxious")
        conv.say("still anxious")                                 # offered
        conv.say("no")                                           # declined
        r = conv.say("ugh, still so anxious and scared")         # stayed, but no re-offer
        self.assertNotIn(frameworks.offer_line("grounding_54321"), r["reply"])

    def test_crisis_overrides_a_pending_offer(self):
        conv = self._conv()
        conv.open()
        conv.say("I'm so anxious")
        conv.say("still anxious")                                 # she offers a tool
        r = conv.say("honestly I just want to die")              # crisis, mid-offer
        self.assertTrue(r["crisis"])
        self.assertIn("109", r["reply"])


if __name__ == "__main__":
    unittest.main()
