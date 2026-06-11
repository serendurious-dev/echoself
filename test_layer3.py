"""tests for the rest of Layer 3: letters, demo mode, echo exchange, soundscape."""

import os
import datetime
import tempfile
import unittest

from core import datastore, session_manager, letters, demo_mode, echo_exchange


class TempData(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()


class TestLetters(TempData):

    def setUp(self):
        super().setUp()
        self.profile = {"your_name": "friend", "ideal_self": {"name": "the steady one"}}

    def test_due_then_not_due_after_writing(self):
        self.assertTrue(letters.due())
        letters.write_monthly(self.profile)
        self.assertFalse(letters.due())

    def test_letter_is_in_the_ideal_self_voice_and_names_the_month(self):
        for i in range(4):
            session_manager.log_mood("ok", 7,
                                     when=datetime.datetime.now() - datetime.timedelta(days=i))
        path = letters.write_monthly(self.profile)
        text = letters.read(path)
        self.assertIn("the steady one", text)
        self.assertIn("friend", text)

    def test_empty_month_is_still_kind(self):
        text = letters.read(letters.write_monthly(self.profile))
        self.assertIn("door stays open", text)

    def test_reply_is_appended_and_kept(self):
        letters.write_monthly(self.profile)
        letters.append_reply("I'm trying. that's all I've got and I think it counts.")
        text = letters.read(letters.letter_path())
        self.assertIn("I'm trying", text)

    def test_all_letters_lists_them(self):
        letters.write_monthly(self.profile)
        self.assertEqual(len(letters.all_letters()), 1)


class TestDemoMode(TempData):

    def test_seed_builds_a_lived_in_month(self):
        demo_mode.seed(days=35)
        self.assertIsNotNone(session_manager.load_profile())
        self.assertTrue(session_manager.load_profile().get("demo"))
        rows = session_manager.read_echo_log()
        self.assertEqual(len({r["date"] for r in rows}), 35)
        model = datastore.load_json("user_model.json")
        self.assertEqual(len(model["state_history"]), 35)
        self.assertGreater(model["drift"]["warmth"], 0)

    def test_seed_has_a_dark_stretch_and_a_recovery(self):
        demo_mode.seed(days=35)
        scores = [int(r["mood_score"]) for r in session_manager.read_echo_log()]
        self.assertLessEqual(min(scores), 3)      # it dipped
        self.assertGreaterEqual(scores[-1], 6)    # and came back up

    def test_ensure_seeded_is_idempotent(self):
        demo_mode.ensure_seeded(days=35)
        n = len(session_manager.read_echo_log())
        demo_mode.ensure_seeded(days=35)          # should not re-seed
        self.assertEqual(len(session_manager.read_echo_log()), n)

    def test_advance_day_adds_one(self):
        demo_mode.seed(days=10)
        before = len({r["date"] for r in session_manager.read_echo_log()})
        demo_mode.advance_day()
        after = len({r["date"] for r in session_manager.read_echo_log()})
        self.assertEqual(after, before + 1)


class TestEchoExchange(unittest.TestCase):

    def test_sentences_load(self):
        pool = echo_exchange.all_sentences()
        self.assertGreaterEqual(len(pool), 3)
        self.assertTrue(all(isinstance(s, str) and s for s in pool))

    def test_random_sentence_is_from_the_pool(self):
        self.assertIn(echo_exchange.random_sentence(), echo_exchange.all_sentences())


class TestSoundscape(unittest.TestCase):

    def test_generate_tone_shape_and_range(self):
        import numpy as np
        from audio import soundscape
        buf = soundscape.generate_tone(0.5, seconds=1.0, rate=8000)
        self.assertEqual(buf.shape, (8000, 2))        # stereo
        self.assertEqual(buf.dtype, np.int16)
        self.assertLessEqual(int(np.abs(buf).max()), 32767)

    def test_closer_is_louder_than_distant(self):
        import numpy as np
        from audio import soundscape
        quiet = np.abs(soundscape.generate_tone(0.0, seconds=1.0, rate=8000)).mean()
        full  = np.abs(soundscape.generate_tone(1.0, seconds=1.0, rate=8000)).mean()
        self.assertGreater(full, quiet)


if __name__ == "__main__":
    unittest.main()
