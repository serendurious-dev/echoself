"""tests for the inner world: archetypes, the brain, the psychology, the drift."""

import os
import datetime
import tempfile
import unittest

from core import datastore, session_manager
from learning import progress_tracker
from ml import archetypes, behavioral_model, psychology_layer
from character import personality_drift


class InnerTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()


class TestArchetypes(unittest.TestCase):

    def test_synthetic_sessions_cover_all_states_reproducibly(self):
        rows, labels = archetypes.synthetic_sessions(per_state=10)
        self.assertEqual(len(rows), 50)
        self.assertEqual(set(labels), set(archetypes.STATES))
        again, _ = archetypes.synthetic_sessions(per_state=10)
        self.assertEqual(rows, again)                  # seeded, same everywhere

    def test_heuristic_recognizes_the_shapes(self):
        #                          acc   dur   hints events lessons gap
        self.assertEqual(archetypes.heuristic_label([0.9, 12.0, 0.1, 14, 2, 1]), "Flowing")
        self.assertEqual(archetypes.heuristic_label([0.4, 40.0, 1.8, 10, 1, 1]), "Pushing")
        self.assertEqual(archetypes.heuristic_label([0.6, 30.0, 0.5, 4, 0, 2]), "Drifting")
        self.assertEqual(archetypes.heuristic_label([0.8, 12.0, 0.2, 3, 0, 4]), "Avoiding")
        self.assertEqual(archetypes.heuristic_label([0.4, 50.0, 0.4, 2, 0, 7]), "Fading")


class TestBrain(InnerTest):

    def test_wakes_without_any_data_at_all(self):
        state = behavioral_model.wake()
        self.assertIn(state, archetypes.STATES)
        model = datastore.load_json(behavioral_model.USER_MODEL)
        self.assertEqual(model["last_state"], state)

    def test_session_zero_signals_color_the_first_guess(self):
        session_manager.save_profile({"session_zero_signals": [
            {"hesitation_s": 1.2, "duration_s": 5.0, "length": 14} for _ in range(8)]})
        self.assertEqual(behavioral_model.wake(), "Flowing")
        session_manager.save_profile({"session_zero_signals": [
            {"hesitation_s": 11.0, "duration_s": 30.0, "length": 3} for _ in range(8)]})
        self.assertEqual(behavioral_model.wake(), "Drifting")

    def test_features_aggregate_by_day(self):
        when = datetime.datetime(2026, 6, 1, 10, 0)
        progress_tracker.log_event("python", 1, "a", "quiz", correct="yes",
                                   duration_s=10, when=when)
        progress_tracker.log_event("python", 1, "a", "lesson_done", when=when)
        progress_tracker.log_event("python", 1, "b", "quiz", correct="no",
                                   duration_s=30, when=when + datetime.timedelta(days=3))
        rows = behavioral_model.session_features()
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(rows[0][0], 1.0)        # day one: all correct
        self.assertEqual(rows[1][5], 3.0)              # day two: the gap

    def test_valence_is_the_seventh_signal(self):
        self.assertEqual(len(archetypes.FEATURES), 7)
        self.assertEqual(archetypes.FEATURES[6], "valence")
        rows, _ = archetypes.synthetic_sessions(per_state=5)
        self.assertEqual(len(rows[0]), 7)

    def test_conversations_color_the_days_valence(self):
        # how you talked that day shows up in the brain's read of the day
        from core import companion
        when = datetime.datetime(2026, 6, 2, 20, 0)
        progress_tracker.log_event("python", 1, "a", "quiz", correct="yes",
                                   duration_s=10, when=when)
        for _ in range(3):
            companion.log_emotion("grief", 0.8, when=when)
        heavy = behavioral_model.session_features()[-1][6]
        self.assertLess(heavy, 0.4)            # grief pulls the day heavy

    def test_a_light_day_reads_light(self):
        from core import companion
        when = datetime.datetime(2026, 6, 2, 20, 0)
        progress_tracker.log_event("python", 1, "a", "quiz", correct="yes",
                                   duration_s=10, when=when)
        companion.log_emotion("joy", 0.8, when=when)
        self.assertGreater(behavioral_model.session_features()[-1][6], 0.8)

    def test_a_withdrawing_history_reads_as_withdrawal(self):
        # busy at first, then thinning out with growing gaps
        base = datetime.datetime(2026, 5, 1, 19, 0)
        for day, n in ((0, 8), (1, 8), (2, 6)):
            for i in range(n):
                progress_tracker.log_event("python", 1, f"l{i}", "quiz", correct="yes",
                                           duration_s=12, when=base + datetime.timedelta(days=day))
        progress_tracker.log_event("python", 1, "x", "quiz", correct="no", duration_s=50,
                                   when=base + datetime.timedelta(days=9))
        state = behavioral_model.wake()
        self.assertIn(state, ("Fading", "Avoiding"))   # both are withdrawal


class TestPsychology(InnerTest):

    def test_every_state_has_a_complete_plan(self):
        for state in archetypes.STATES:
            plan = psychology_layer.plan_for(state)
            for field in ("mode", "expression", "opening_slot", "hesitation_s", "state"):
                self.assertIn(field, plan)

    def test_fading_brings_the_memory(self):
        progress_tracker.log_event("python", 1, "py-c1-l1", "lesson_done")
        plan = psychology_layer.plan_for("Fading")
        self.assertEqual(plan["mode"], "Memory")
        self.assertIn("1 lesson", plan["memory_line"])

    def test_drifting_offers_the_sky(self):
        self.assertTrue(psychology_layer.plan_for("Drifting").get("offer_drift"))

    def test_planning_nudges_the_drift(self):
        psychology_layer.plan_for("Flowing")
        drift = personality_drift.load()
        self.assertGreater(drift["challenge"], 0.0)


class TestDrift(InnerTest):

    def test_axes_stay_bounded(self):
        drift = personality_drift.load()
        for _ in range(100):
            personality_drift.nudge(drift, "Fading")
        self.assertEqual(drift["warmth"], 1.0)
        self.assertGreaterEqual(drift["challenge"], -1.0)

    def test_warmth_stretches_patience_challenge_shortens_it(self):
        base = 14.0
        warm = {"challenge": 0.0, "warmth": 0.8, "pace": 0.0}
        hard = {"challenge": 0.8, "warmth": 0.0, "pace": 0.0}
        self.assertGreater(personality_drift.pace_hesitation(warm, base), base)
        self.assertLess(personality_drift.pace_hesitation(hard, base), base)

    def test_drift_survives_the_roundtrip(self):
        drift = personality_drift.load()
        personality_drift.nudge(drift, "Pushing")
        personality_drift.save(drift)
        again = personality_drift.load()
        self.assertAlmostEqual(again["warmth"], drift["warmth"], places=4)


if __name__ == "__main__":
    unittest.main()
