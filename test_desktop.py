"""the desktop window launcher - gated on pywebview, never fatal without it."""

import io
import contextlib
import unittest

import desktop


class TestDesktop(unittest.TestCase):

    def test_available_is_a_bool(self):
        self.assertIn(desktop.available(), (True, False))

    def test_launch_without_pywebview_falls_back_to_the_browser(self):
        # force the missing-toolkit path so the test never opens a real window. it must
        # not raise, and it must point the user at the browser route instead.
        real = desktop.available
        desktop.available = lambda: False
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                result = desktop.launch(8765)
            self.assertIsNone(result)
            self.assertIn("browser", out.getvalue().lower())
            self.assertIn("--serve", out.getvalue())
        finally:
            desktop.available = real


if __name__ == "__main__":
    unittest.main()
