"""tests for data ownership: export to a zip, forget entirely."""

import os
import zipfile
import tempfile
import unittest

from core import datastore, data_control, session_manager


class DataControlTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._out = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()
        self._out.cleanup()

    def _seed(self):
        session_manager.save_profile({"your_name": "Aria"})
        session_manager.log_mood("okay", 6)

    def test_export_zips_the_data(self):
        self._seed()
        path = data_control.export(dest_dir=self._out.name)
        self.assertTrue(os.path.exists(path) and path.endswith(".zip"))
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
        self.assertIn("profile.json", names)
        self.assertIn("echo_log.csv", names)

    def test_export_on_empty_data_still_makes_a_zip(self):
        path = data_control.export(dest_dir=self._out.name)
        self.assertTrue(os.path.exists(path))

    def test_forget_removes_everything(self):
        self._seed()
        self.assertIsNotNone(session_manager.load_profile())
        removed = data_control.forget()
        self.assertIn("profile.json", removed)
        self.assertIsNone(session_manager.load_profile())
        self.assertEqual(session_manager.read_echo_log(), [])

    def test_forget_on_empty_is_harmless(self):
        self.assertEqual(data_control.forget(), [])


if __name__ == "__main__":
    unittest.main()
