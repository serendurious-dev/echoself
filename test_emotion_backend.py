"""the pluggable emotion read: lexicon floor, optional transformer backend."""

import unittest

from core import emotion, emotion_nn


class TestBackendSeam(unittest.TestCase):

    def tearDown(self):
        emotion.clear_backend()

    def test_lexicon_is_the_default(self):
        emotion.clear_backend()
        self.assertEqual(emotion.analyze("i'm so anxious")["primary"], "fear")

    def test_a_backend_is_used_when_wired(self):
        emotion.set_backend(lambda t: {"primary": "joy", "secondary": None,
                                       "intensity": 0.9, "confidence": 0.9, "scores": {}})
        self.assertEqual(emotion.analyze("anything at all")["primary"], "joy")
        self.assertEqual(emotion.detect("anything at all")[0], "joy")

    def test_a_broken_backend_falls_back_to_the_lexicon(self):
        def boom(text):
            raise RuntimeError("model down")
        emotion.set_backend(boom)
        self.assertEqual(emotion.analyze("i'm so anxious")["primary"], "fear")


class TestTransformerBackend(unittest.TestCase):
    # the hybrid logic is pure and testable without installing torch

    def test_available_returns_a_bool(self):
        self.assertIn(emotion_nn.available(), (True, False))

    def test_label_mapping(self):
        self.assertEqual(emotion_nn._label_to_emotion("sadness"), "sadness")
        self.assertEqual(emotion_nn._label_to_emotion("disgust"), "anger")
        self.assertEqual(emotion_nn._label_to_emotion("surprise"), "joy")
        self.assertEqual(emotion_nn._label_to_emotion("whatever"), "neutral")

    def test_lexicon_keeps_a_fine_feeling_the_model_cant_name(self):
        # model says "sadness"; lexicon clearly sees shame -> shame wins
        lex = {"primary": "shame", "secondary": None, "intensity": 0.6,
               "confidence": 0.8, "scores": {}}
        out = emotion_nn._blend("sadness", 0.95, lex)
        self.assertEqual(out["primary"], "shame")

    def test_model_wins_when_lexicon_has_no_fine_read(self):
        lex = {"primary": "sadness", "secondary": None, "intensity": 0.3,
               "confidence": 0.4, "scores": {}}
        out = emotion_nn._blend("fear", 0.9, lex)
        self.assertEqual(out["primary"], "fear")
        self.assertEqual(out["confidence"], 0.9)


if __name__ == "__main__":
    unittest.main()
