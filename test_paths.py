"""the one place that knows dev from a packaged build - assets vs writable data."""

import os
import sys
import unittest

from core import paths


class TestPaths(unittest.TestCase):

    def test_from_source_everything_is_the_repo(self):
        # not frozen: assets and data both resolve to the repo, and the content's there
        self.assertEqual(paths.data_root(), paths.resource_root())
        self.assertTrue(os.path.isdir(os.path.join(paths.resource_root(), "lessons")))

    def test_packaged_splits_assets_from_writable_data(self):
        sys.frozen = True
        sys._MEIPASS = os.path.join("x", "bundle")
        try:
            # bundled assets come from the unpack dir...
            self.assertEqual(paths.resource_root(), sys._MEIPASS)
            # ...but the user's data must NOT live in the throwaway bundle
            self.assertNotEqual(paths.data_root(), sys._MEIPASS)
            self.assertIn("EchoSelf", paths.data_root())
        finally:
            del sys.frozen
            del sys._MEIPASS


if __name__ == "__main__":
    unittest.main()
