"""DBT distress tolerance: the acute skills, offered when a feeling peaks."""

import unittest

from psychology import frameworks
from core.companion import Conversation


class TestDbtFrameworks(unittest.TestCase):

    def test_skills_exist_with_offer_walk_and_source(self):
        for key in ("dbt_tipp", "dbt_stop", "dbt_radical_acceptance", "dbt_self_soothe"):
            fw = frameworks.get(key)
            self.assertIsNotNone(fw, key)
            self.assertTrue(fw["offer"] and fw["walk"] and fw["source"], key)


class TestAcuteOffer(unittest.TestCase):
    # the offer lands on the continuation turn (when you've stayed on a feeling)

    def test_panic_gets_tipp_then_walks_it(self):
        c = Conversation()
        c.say("i'm so terrified and panicking and scared")
        r = c.say("i'm so terrified and panicking and scared")
        self.assertIn(frameworks.offer_line("dbt_tipp"), r["reply"])
        walked = c.say("yes")
        self.assertEqual(walked["reply"], frameworks.walk("dbt_tipp"))

    def test_mild_fear_gets_the_gentler_grounding(self):
        c = Conversation()
        c.say("i'm a bit anxious")
        r = c.say("i'm a bit anxious")
        self.assertIn(frameworks.offer_line("grounding_54321"), r["reply"])

    def test_grief_offers_radical_acceptance(self):
        c = Conversation()
        c.say("i'm grieving and i miss them so much")
        r = c.say("i'm grieving and i miss them so much")
        self.assertIn(frameworks.offer_line("dbt_radical_acceptance"), r["reply"])

    def test_numbness_offers_self_soothe(self):
        c = Conversation()
        c.say("i feel hollow and detached and blank")
        r = c.say("i feel hollow and detached and blank")
        self.assertIn(frameworks.offer_line("dbt_self_soothe"), r["reply"])


if __name__ == "__main__":
    unittest.main()
