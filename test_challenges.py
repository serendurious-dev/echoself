"""tests for the editor-handoff challenge system: the runner and the gating."""

import os
import datetime
import tempfile
import unittest

from learning import codepath, challenge_runner, progress_tracker
from core import datastore

CHALLENGE = {
    "id": "test-even", "title": "Even", "kind": "challenge", "cluster": 1,
    "prompt": "is_even", "function": "is_even",
    "starter": "def is_even(n):\n    pass\n",
    "cases": [{"args": [4], "expect": True}, {"args": [7], "expect": False}],
    "hints": ["a", "b", "c"],
}


class RunnerTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = challenge_runner.WORKSPACE
        challenge_runner.WORKSPACE = self._tmp.name

    def tearDown(self):
        challenge_runner.WORKSPACE = self._old
        self._tmp.cleanup()

    def _solve(self, body):
        with open(challenge_runner.starter_path(CHALLENGE), "w", encoding="utf-8") as f:
            f.write(body)

    def test_starter_is_written_and_not_clobbered(self):
        path = challenge_runner.write_starter(CHALLENGE)
        self.assertTrue(os.path.exists(path))
        self._solve("def is_even(n): return True  # my work")
        challenge_runner.write_starter(CHALLENGE)            # must not overwrite
        with open(path, encoding="utf-8") as f:
            self.assertIn("my work", f.read())

    def test_a_correct_solution_passes(self):
        challenge_runner.write_starter(CHALLENGE)
        self._solve("def is_even(n):\n    return n % 2 == 0\n")
        passed, detail = challenge_runner.run(CHALLENGE)
        self.assertTrue(passed, detail)
        self.assertIn("PASS", detail)

    def test_a_wrong_solution_fails_with_the_case(self):
        challenge_runner.write_starter(CHALLENGE)
        self._solve("def is_even(n):\n    return False\n")
        passed, detail = challenge_runner.run(CHALLENGE)
        self.assertFalse(passed)
        self.assertIn("FAIL", detail)

    def test_a_broken_file_is_reported_not_crashing(self):
        challenge_runner.write_starter(CHALLENGE)
        self._solve("def is_even(n)\n    return True\n")     # syntax error
        passed, detail = challenge_runner.run(CHALLENGE)
        self.assertFalse(passed)

    def test_running_before_solving_is_handled(self):
        passed, detail = challenge_runner.run(CHALLENGE)
        self.assertFalse(passed)
        self.assertIn("starter", detail)


class GatingTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def _finish_cluster_one(self):
        for lesson in [l for l in codepath.load_track("python") if l["cluster"] == 1]:
            progress_tracker.log_event("python", 1, lesson["id"], "lesson_done")

    def test_real_content_loads_as_challenges(self):
        extras = codepath.load_extras("python")
        ids = [e["id"] for e in extras]
        self.assertIn("py-c1-challenge", ids)
        self.assertIn("py-c1-project", ids)
        # a challenge sorts before its project
        self.assertLess(ids.index("py-c1-challenge"), ids.index("py-c1-project"))

    def test_challenge_is_locked_until_the_lessons_are_done(self):
        self.assertIsNone(codepath.next_challenge("python"))   # nothing unlocked yet
        self._finish_cluster_one()
        self.assertEqual(codepath.next_challenge("python")["id"], "py-c1-challenge")

    def test_project_waits_for_the_challenge(self):
        self._finish_cluster_one()
        self.assertEqual(codepath.next_challenge("python")["kind"], "challenge")
        progress_tracker.log_event("python", 1, "py-c1-challenge", "challenge_done")
        self.assertEqual(codepath.next_challenge("python")["id"], "py-c1-project")
        progress_tracker.log_event("python", 1, "py-c1-project", "challenge_done")
        # cluster one fully done -> nothing more unlocked here yet
        nxt = codepath.next_challenge("python")
        self.assertNotIn((nxt or {}).get("cluster"), (1,)) if nxt else self.assertIsNone(nxt)


if __name__ == "__main__":
    unittest.main()
