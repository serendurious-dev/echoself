"""the headless core: the contract every frontend drives the brain through."""

import tempfile
import unittest

from core import datastore
import echoself_core


class TestCoreApi(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name
        self.profile = {"ideal_self": {"name": "the steady one"}, "your_name": "me"}

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_no_profile_means_onboarding(self):
        self.assertTrue(echoself_core.needs_onboarding())
        self.assertTrue(echoself_core.boot()["needs_onboarding"])

    def test_today_is_the_days_answer(self):
        state = echoself_core.today(self.profile)
        for key in ("plan", "distance", "closeness"):
            self.assertIn(key, state)
        self.assertEqual(set(state["distance"]),
                         {"mental", "behavioral", "emotional", "learning"})
        self.assertTrue(0.0 <= state["closeness"] <= 1.0)

    def test_respond_passes_through_and_crisis_stays(self):
        self.assertTrue(echoself_core.respond("I want to die")["crisis"])
        self.assertFalse(echoself_core.respond("I feel so empty")["crisis"])

    def test_reads_emotion_and_crisis(self):
        self.assertEqual(echoself_core.read_emotion("I'm so anxious")["primary"], "fear")
        self.assertTrue(echoself_core.is_crisis("I want to die"))
        self.assertFalse(echoself_core.is_crisis("just tired today"))

    def test_a_conversation_can_be_opened(self):
        convo = echoself_core.conversation()
        self.assertTrue(hasattr(convo, "say"))
        self.assertTrue(hasattr(convo, "open"))


class TestLearningAndMemorySurface(unittest.TestCase):
    # the learning + portrait flows a frontend needs, through the core

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_mastery_report_and_tracks(self):
        report = echoself_core.mastery_report()
        self.assertIn("track", report)
        tracks = echoself_core.learning_tracks()
        self.assertTrue(any(t[0] == "python" for t in tracks))

    def test_set_track_sticks(self):
        echoself_core.set_learning_track("java")
        self.assertEqual(echoself_core.mastery_report()["track"], "java")

    def test_portrait_facts_and_forget(self):
        from core import portrait
        portrait.remember("thesis is hanging over them", kind="weight", source="you")
        facts = echoself_core.portrait_facts()
        self.assertTrue(facts)
        echoself_core.forget_fact(facts[0]["id"])
        self.assertEqual(len(echoself_core.portrait_facts()), len(facts) - 1)


class TestWarmVoiceWiring(unittest.TestCase):
    # the model layer reached through the core: mode follows availability,
    # research delegates. no key needed - the layer is mocked.

    def setUp(self):
        from core import llm
        self.llm = llm
        self._av, self._rs = llm.available, llm.research

    def tearDown(self):
        self.llm.available, self.llm.research = self._av, self._rs

    def test_mode_follows_availability(self):
        self.llm.available = lambda: False
        self.assertEqual(echoself_core.companion_mode(), "offline")
        self.assertFalse(echoself_core.llm_available())
        self.llm.available = lambda: True
        self.assertEqual(echoself_core.companion_mode(), "warm")

    def test_research_delegates_to_the_layer(self):
        self.llm.research = lambda q: f"looked up: {q}"
        self.assertEqual(echoself_core.research("seoul weather"), "looked up: seoul weather")


if __name__ == "__main__":
    unittest.main()
