"""tests for piece 3 - she reaches out. settings the user owns, a notification
that degrades to a log line, and the once-a-day/waking-hours/not-if-you-came-by
decision, all offline and read from the user's own clock."""

import os
import datetime
import tempfile
import unittest

from core import (settings, notify, outreach, companion, session_manager,
                  portrait, datastore)


class _DataDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()


class TestSettings(_DataDir):

    def test_defaults_then_changes_persist(self):
        self.assertTrue(settings.get("outreach"))
        self.assertEqual(settings.get("outreach_style"), "general")
        self.assertFalse(settings.toggle_outreach())
        self.assertEqual(settings.toggle_style(), "personal")
        # reload from disk to be sure it saved
        self.assertFalse(settings.get("outreach"))
        self.assertEqual(settings.get("outreach_style"), "personal")


class TestNotifyFallback(_DataDir):

    def test_falls_back_to_the_log_line(self):
        # force the toast to fail (so this holds on any box, and pops nothing during
        # tests): it must fall back and still never lose the message
        real = notify._toast_windows

        def boom(*a):
            raise RuntimeError("no toast here")

        notify._toast_windows = boom
        try:
            fired = notify.notify("EchoSelf", "how was today?")
        finally:
            notify._toast_windows = real
        self.assertFalse(fired)
        with open(os.path.join(datastore.DATA_DIR, "reminders.log"), encoding="utf-8") as f:
            self.assertIn("how was today?", f.read())


class TestOutreachDecision(_DataDir):

    def _afternoon(self):
        return datetime.datetime(2026, 6, 13, 14, 0)

    def test_reaches_out_in_waking_hours_when_you_havent_come_by(self):
        self.assertTrue(outreach.should_reach(now=self._afternoon()))

    def test_not_in_the_dead_of_night(self):
        self.assertFalse(outreach.should_reach(now=datetime.datetime(2026, 6, 13, 3, 0)))

    def test_not_if_you_already_showed_up_today(self):
        session_manager.log_mood("okay", 6)        # logs today
        self.assertFalse(outreach.should_reach(now=self._afternoon()))

    def test_not_if_turned_off(self):
        settings.set("outreach", False)
        self.assertFalse(outreach.should_reach(now=self._afternoon()))

    def test_not_twice_in_a_day(self):
        self.assertFalse(outreach.should_reach(now=self._afternoon(), already_today=True))


class TestOutreachWording(_DataDir):

    def test_general_fits_the_time_of_day(self):
        self.assertEqual(outreach.compose(now=datetime.datetime(2026, 6, 13, 9, 0),
                                          style="general"), "morning. how are you today?")

    def test_personal_leans_on_the_portrait(self):
        portrait.remember("the thesis", kind="weight", when=datetime.date.today())
        line = outreach.compose(now=datetime.datetime(2026, 6, 13, 14, 0), style="personal")
        self.assertIn("thesis", line)

    def test_a_heavy_stretch_softens_everything(self):
        for _ in range(4):
            companion.log_emotion("sadness", 0.7)
        line = outreach.compose(now=datetime.datetime(2026, 6, 13, 9, 0), style="personal")
        self.assertIn("here whenever you want to talk", line)


class TestDaemonReachesOutOncePerDay(_DataDir):

    def test_marker_stops_a_second_send(self):
        from osutil import daemon
        sent = {"n": 0}
        real = notify.notify
        outreach_real = outreach.should_reach
        notify.notify = lambda *a: sent.__setitem__("n", sent["n"] + 1) or True
        outreach.should_reach = lambda *a, **k: True
        try:
            self.assertTrue(daemon._reach_out(datastore.DATA_DIR))
            self.assertFalse(daemon._reach_out(datastore.DATA_DIR))   # already today
            self.assertEqual(sent["n"], 1)
        finally:
            notify.notify = real
            outreach.should_reach = outreach_real


if __name__ == "__main__":
    unittest.main()
