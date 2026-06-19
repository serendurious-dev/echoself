"""ACT: unhooking from a fused thought, and a step back toward what matters."""

import unittest

from psychology import frameworks
from core.companion import Conversation


class TestActFrameworks(unittest.TestCase):

    def test_skills_exist_with_offer_walk_and_source(self):
        for key in ("act_defusion", "act_values"):
            fw = frameworks.get(key)
            self.assertIsNotNone(fw, key)
            self.assertTrue(fw["offer"] and fw["walk"] and fw["source"], key)


class TestActOffer(unittest.TestCase):

    def test_deep_shame_gets_defusion_then_walks_it(self):
        c = Conversation()
        c.say("i'm such a worthless failure, completely useless")
        r = c.say("i'm such a worthless failure, completely useless")
        self.assertIn(frameworks.offer_line("act_defusion"), r["reply"])
        walked = c.say("yes")
        self.assertEqual(walked["reply"], frameworks.walk("act_defusion"))

    def test_mild_shame_gets_self_compassion(self):
        c = Conversation()
        c.say("i feel a bit ashamed about it")
        r = c.say("i feel a bit ashamed about it")
        self.assertIn(frameworks.offer_line("self_compassion"), r["reply"])

    def test_deep_numbness_gets_values(self):
        c = Conversation()
        c.say("i feel completely hollow and detached and blank and flat")
        r = c.say("i feel completely hollow and detached and blank and flat")
        self.assertIn(frameworks.offer_line("act_values"), r["reply"])

    def test_mild_numbness_gets_self_soothe(self):
        c = Conversation()
        c.say("i feel a bit hollow")
        r = c.say("i feel a bit hollow")
        self.assertIn(frameworks.offer_line("dbt_self_soothe"), r["reply"])


if __name__ == "__main__":
    unittest.main()
