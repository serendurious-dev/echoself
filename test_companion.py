"""tests for reading emotion from text and responding with care - especially crisis safety."""

import tempfile
import unittest

from core import emotion, companion, datastore


class TestEmotion(unittest.TestCase):

    def test_reads_each_emotion(self):
        cases = {
            "honestly I feel so empty and tired lately": "sadness",
            "I'm furious, it was completely unfair": "anger",
            "I'm so anxious and overwhelmed about tomorrow": "fear",
            "nobody sees me, I feel invisible": "loneliness",
            "I'm such a failure, I'm not good enough": "shame",
            "today was wonderful, I feel hopeful and proud": "joy",
        }
        for text, expected in cases.items():
            self.assertEqual(emotion.detect(text)[0], expected, text)

    def test_negation_flips_positive(self):
        self.assertEqual(emotion.detect("I'm not happy")[0], "sadness")

    def test_neutral_when_nothing_registers(self):
        emo, intensity, _ = emotion.detect("the meeting is at three on tuesday")
        self.assertEqual(emo, "neutral")
        self.assertEqual(intensity, 0.0)

    def test_intensity_grows_with_more_signal(self):
        weak = emotion.detect("a bit sad")[1]
        strong = emotion.detect("so sad, empty, hopeless and exhausted")[1]
        self.assertGreater(strong, weak)

    def test_crisis_is_detected(self):
        for t in ["I want to die", "I can't go on anymore", "thinking about ending it all",
                  "I don't want to live"]:
            self.assertTrue(emotion.is_crisis(t), t)
        self.assertFalse(emotion.is_crisis("I'm just tired today"))


class TestCompanion(unittest.TestCase):

    def test_crisis_overrides_everything(self):
        # even wrapped in other feelings, crisis wins and brings real-help guidance
        r = companion.respond("I'm so tired of everything, I want to die")
        self.assertTrue(r["crisis"])
        self.assertEqual(r["emotion"], "crisis")
        self.assertIn("109", r["reply"])
        self.assertIn("not a person who can keep you safe", r["reply"])

    def test_answers_from_the_right_stance(self):
        r = companion.respond("I feel so alone, nobody sees me")
        self.assertEqual(r["emotion"], "loneliness")
        self.assertFalse(r["crisis"])
        self.assertIn(r["reply"], companion.RESPONSES["loneliness"]["lines"])

    def test_neutral_opens_a_door(self):
        r = companion.respond("we shipped the report")
        self.assertEqual(r["emotion"], "neutral")
        self.assertIn(r["reply"], companion.RESPONSES["neutral"]["lines"])

    def test_llm_seam_is_used_when_given(self):
        called = {}

        def fake_llm(text, emo, stance):
            called["args"] = (text, emo, stance)
            return "a warmer, model-written reply"

        r = companion.respond("I'm really anxious", llm=fake_llm)
        self.assertEqual(r["reply"], "a warmer, model-written reply")
        self.assertEqual(called["args"][1], "fear")

    def test_llm_failure_falls_back_to_the_library(self):
        def broken_llm(*a):
            raise RuntimeError("no network")

        r = companion.respond("I feel empty", llm=broken_llm)
        self.assertIn(r["reply"], companion.RESPONSES["sadness"]["lines"])

    def test_crisis_never_reaches_the_llm(self):
        def llm_should_not_run(*a):
            raise AssertionError("the LLM must never handle a crisis message")

        r = companion.respond("I want to die", llm=llm_should_not_run)
        self.assertTrue(r["crisis"])


class TestEmotionLog(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_logs_the_signal_not_the_words(self):
        companion.log_emotion("sadness", 0.7)
        rows = companion.recent_emotions()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["emotion"], "sadness")
        # the conversation log has no column for what was typed
        self.assertNotIn("text", rows[0])
        self.assertNotIn("message", rows[0])


class TestInjectableWordingSeam(unittest.TestCase):
    # EchoSelf ships no external brain - it runs fully offline. but the wording is
    # pluggable: respond() takes an optional callable. these tests pin that seam
    # down with fakes, including that it stays offline by default and that a crisis
    # never reaches anything injected.

    def test_offline_by_default_no_seam_wired(self):
        # with nothing injected, the answer always comes from the offline library
        r = companion.respond("I feel so empty")
        self.assertIn(r["reply"], companion.RESPONSES["sadness"]["lines"])

    def test_an_injected_engine_is_used(self):
        r = companion.respond("I'm a little anxious", llm=lambda *a: "an injected line")
        self.assertEqual(r["reply"], "an injected line")

    def test_injected_failure_falls_back_to_the_library(self):
        def down(*a):
            raise RuntimeError("boom")
        r = companion.respond("I feel so empty", llm=down)
        self.assertIn(r["reply"], companion.RESPONSES["sadness"]["lines"])

    def test_crisis_never_reaches_an_injected_engine(self):
        def must_not_run(*a):
            raise AssertionError("a crisis message must never reach an injected engine")
        r = companion.respond("I want to die", llm=must_not_run)
        self.assertTrue(r["crisis"])


class TestEmotionFeedsTheInnerWorld(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_an_emotion_drifts_the_personality(self):
        from character import personality_drift
        d = {"challenge": 0.0, "warmth": 0.0, "pace": 0.0}
        personality_drift.nudge_emotion(d, "loneliness")
        self.assertGreater(d["warmth"], 0.0)
        personality_drift.nudge_emotion(d, "joy")
        self.assertGreater(d["challenge"], 0.0)

    def test_heavy_conversations_open_the_emotional_gap(self):
        from core import echo_distance
        for _ in range(5):
            companion.log_emotion("sadness", 0.7)
        self.assertGreater(echo_distance.compute()["emotional"], 0.6)

    def test_joyful_conversations_close_it(self):
        from core import echo_distance
        for _ in range(5):
            companion.log_emotion("joy", 0.8)
        self.assertLess(echo_distance.compute()["emotional"], 0.3)


if __name__ == "__main__":
    unittest.main()
