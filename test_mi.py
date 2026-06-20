"""motivational interviewing: meeting ambivalence with reflection, not a push."""

import unittest

from psychology import mi
from core.companion import Conversation


class TestMI(unittest.TestCase):

    def test_detects_explicit_ambivalence(self):
        self.assertTrue(mi.is_ambivalent("i want to but i can't get started"))
        self.assertTrue(mi.is_ambivalent("i know i should call them"))
        self.assertFalse(mi.is_ambivalent("i feel sad today"))
        self.assertFalse(mi.is_ambivalent("today was good"))

    def test_talk_reflects_ambivalence_without_pushing(self):
        c = Conversation()
        r = c.say("i know i should reach out but i keep putting it off")
        self.assertIn(r["reply"], mi._REFLECTIONS)
        self.assertFalse(r["crisis"])

    def test_a_plain_feeling_is_not_treated_as_ambivalence(self):
        c = Conversation()
        r = c.say("i feel really anxious")
        self.assertNotIn(r["reply"], mi._REFLECTIONS)


if __name__ == "__main__":
    unittest.main()
