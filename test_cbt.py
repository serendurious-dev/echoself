"""CBT: a thought record for harsh thoughts, behavioral activation for the heavy days."""

import unittest

from psychology import frameworks
from core.companion import Conversation


class TestCbtFrameworks(unittest.TestCase):

    def test_skills_exist_with_offer_walk_and_source(self):
        for key in ("cbt_thought_record", "behavioral_activation"):
            fw = frameworks.get(key)
            self.assertIsNotNone(fw, key)
            self.assertTrue(fw["offer"] and fw["walk"] and fw["source"], key)


class TestCbtOffer(unittest.TestCase):

    def test_low_mood_offers_behavioral_activation(self):
        c = Conversation()
        c.say("i feel so down and heavy and hopeless lately")
        r = c.say("i feel so down and heavy and hopeless lately")
        self.assertIn(frameworks.offer_line("behavioral_activation"), r["reply"])
        walked = c.say("yes")
        self.assertEqual(walked["reply"], frameworks.walk("behavioral_activation"))

    def test_intense_guilt_gets_the_full_thought_record(self):
        c = Conversation()
        c.say("it's all my fault, i let everyone down")
        r = c.say("it's all my fault, i let everyone down")
        self.assertIn(frameworks.offer_line("cbt_thought_record"), r["reply"])

    def test_mild_guilt_gets_the_gentler_reframe(self):
        c = Conversation()
        c.say("i feel a bit guilty about it")
        r = c.say("i feel a bit guilty about it")
        self.assertIn(frameworks.offer_line("cbt_reframe"), r["reply"])


if __name__ == "__main__":
    unittest.main()
