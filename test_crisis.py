"""crisis safety: the right lines for the region, deterministic and offline."""

import tempfile
import unittest

from core import crisis, companion, datastore, settings


class TestCrisisResources(unittest.TestCase):

    def test_default_region_is_korea(self):
        self.assertTrue(any("109" in line for line in crisis.resources_for(None)))

    def test_a_known_region_swaps_the_local_line(self):
        lines = crisis.resources_for("US")
        self.assertTrue(any("988" in line for line in lines))
        self.assertFalse(any("109" in line for line in lines))

    def test_international_help_is_always_there(self):
        for region in (None, "US", "ZZ"):
            self.assertTrue(any("emergency number" in line
                                for line in crisis.resources_for(region)))

    def test_reply_keeps_the_care_and_carries_the_line(self):
        r = crisis.reply("US")
        self.assertIn("not a person who can keep you safe", r)
        self.assertIn("988", r)


class TestCrisisInCompanion(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_default_points_to_korea(self):
        r = companion.respond("I want to die")
        self.assertTrue(r["crisis"])
        self.assertIn("109", r["reply"])

    def test_region_setting_changes_the_lines(self):
        settings.set("region", "US")
        r = companion.respond("I want to die")
        self.assertTrue(r["crisis"])
        self.assertIn("988", r["reply"])
        self.assertNotIn("109", r["reply"])


if __name__ == "__main__":
    unittest.main()
