"""reflective listening: she mirrors back the thing you named, the mirror-self made
literal - and stays quiet rather than mirror it wrong."""

import os
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from psychology import reflection
from core import datastore


class TestReflection(unittest.TestCase):

    def test_pulls_the_named_thing_and_shifts_to_you(self):
        self.assertEqual(reflection.topic("i'm so behind on my thesis"), "your thesis")
        self.assertEqual(reflection.topic("i had a fight with my mom today"), "your mom")

    def test_about_and_because_topics(self):
        self.assertEqual(reflection.topic("i'm anxious about the job interview tomorrow"),
                         "job interview")
        self.assertEqual(reflection.topic("everything hurts because of the breakup"),
                         "breakup")

    def test_trims_a_clause_back_to_the_thing(self):
        # "my boss never listens" is a clause; the thing is the boss
        self.assertEqual(reflection.topic("i hate that my boss never listens to me"),
                         "your boss")

    def test_says_nothing_when_there_is_no_clean_topic(self):
        for t in ("i feel empty", "idk", "about it too", ""):
            self.assertIsNone(reflection.topic(t), t)

    def test_lead_wraps_the_topic(self):
        line = reflection.lead("your thesis")
        self.assertIn("your thesis", line)


class TestReflectionInConversation(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_she_mirrors_a_named_topic_once(self):
        from core import companion
        c = companion.Conversation()
        c.open()
        r1 = c.say("i am so behind on my thesis and i feel useless")
        self.assertIn("your thesis", r1["reply"])
        # same topic again -> she doesn't mirror it a second time (no tic)
        r2 = c.say("my thesis is still wrecking me")
        self.assertNotIn("your thesis", r2["reply"])


if __name__ == "__main__":
    unittest.main()
