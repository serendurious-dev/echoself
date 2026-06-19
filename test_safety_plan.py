"""the safety plan: yours, private, surfaced gently in a crisis."""

import tempfile
import unittest

from core import safety_plan, companion, datastore


class TestSafetyPlan(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_starts_empty(self):
        self.assertFalse(safety_plan.has_content())
        self.assertEqual(safety_plan.load()["what_helps"], [])

    def test_add_persists(self):
        safety_plan.add("what_helps", "step outside for air")
        self.assertTrue(safety_plan.has_content())
        self.assertIn("step outside for air", safety_plan.load()["what_helps"])

    def test_remove(self):
        safety_plan.add("people", "mom")
        safety_plan.remove("people", 0)
        self.assertEqual(safety_plan.load()["people"], [])

    def test_ignores_unknown_section_and_blank(self):
        safety_plan.add("nope", "x")
        safety_plan.add("people", "   ")
        self.assertFalse(safety_plan.has_content())

    def test_summary_carries_items_and_crisis_lines(self):
        safety_plan.add("reasons", "my dog needs me")
        s = safety_plan.summary("US")
        self.assertIn("my dog needs me", s)
        self.assertIn("988", s)


class TestSafetyPlanInCrisis(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_crisis_points_to_the_plan_when_it_exists(self):
        safety_plan.add("what_helps", "call a friend")
        r = companion.respond("I want to die")
        self.assertTrue(r["crisis"])
        self.assertIn("plan you wrote", r["reply"])
        self.assertIn("109", r["reply"])      # the human-help push is still there

    def test_crisis_has_no_pointer_without_a_plan(self):
        r = companion.respond("I want to die")
        self.assertTrue(r["crisis"])
        self.assertNotIn("plan you wrote", r["reply"])


if __name__ == "__main__":
    unittest.main()
