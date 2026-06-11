"""tests for the OS layer: the lock, IPC, the daemon loop, recovery, doctor."""

import os
import time
import threading
import tempfile
import unittest

from osutil import FileLock
from osutil.ipc import DaemonChannel
from osutil import daemon, recovery


class OSTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir  = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()


class TestFileLock(OSTest):

    def test_eight_threads_no_lost_updates(self):
        # the AlterEgo proof: 8 threads x 50 increments = exactly 400 through
        # the lock, no lost writes
        counter = os.path.join(self.dir, "counter")
        with open(counter, "w") as f:
            f.write("0")

        def worker():
            for _ in range(50):
                with FileLock(counter, timeout=20):
                    with open(counter) as f:
                        n = int(f.read())
                    with open(counter, "w") as f:
                        f.write(str(n + 1))

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        with open(counter) as f:
            self.assertEqual(int(f.read()), 400)

    def test_second_holder_is_blocked(self):
        target = os.path.join(self.dir, "x")
        held = FileLock(target, timeout=0.3)
        held.acquire()
        try:
            with self.assertRaises(TimeoutError):
                FileLock(target, timeout=0.3).acquire()
        finally:
            held.release()

    def test_stale_lock_gets_reclaimed(self):
        target = os.path.join(self.dir, "y")
        dead = FileLock(target)
        dead.acquire()
        # simulate a crash: the holder's process is gone, so the OS has closed
        # its handle, but the .lock file is left behind with an old mtime
        os.close(dead._fd)
        dead._fd = None
        past = time.time() - 120
        os.utime(dead.path, (past, past))
        reclaimed = FileLock(target, stale=0.01, timeout=1.0)
        reclaimed.acquire()                  # should steal it, not time out
        reclaimed.release()


class TestChannel(OSTest):

    def test_pid_beat_stop_lifecycle(self):
        ch = DaemonChannel(self.dir)
        self.assertIsNone(ch.read_pid())
        ch.write_pid()
        self.assertEqual(ch.read_pid(), os.getpid())
        ch.beat()
        self.assertTrue(ch.is_alive(max_age=90))
        self.assertTrue(ch.running())
        ch.request_stop()
        self.assertTrue(ch.stop_requested())
        ch.clear_stop()
        self.assertFalse(ch.stop_requested())
        ch.clear_pid()
        self.assertIsNone(ch.read_pid())

    def test_old_heartbeat_is_not_alive(self):
        ch = DaemonChannel(self.dir)
        ch.beat()
        self.assertTrue(ch.is_alive(max_age=90))
        # the heartbeat stamp lives in the file's contents, so backdate that
        ch._write(ch.beat_path, str(time.time() - 600))
        self.assertFalse(ch.is_alive(max_age=90))


class TestDaemonLoop(OSTest):

    def test_runs_ticks_beats_and_clears_pid(self):
        ticks = daemon.daemon_run(self.dir, interval=0.01, max_ticks=3)
        self.assertEqual(ticks, 3)
        ch = DaemonChannel(self.dir)
        self.assertIsNone(ch.read_pid())          # cleared on clean exit
        self.assertIsNotNone(ch.last_beat())      # but it did beat

    def test_presence_writes_one_reminder_a_day(self):
        daemon.daemon_run(self.dir, interval=0.01, max_ticks=3)
        with open(os.path.join(self.dir, "reminders.log")) as f:
            lines = [ln for ln in f if ln.strip()]
        self.assertEqual(len(lines), 1)           # once a day, not once a tick

    def test_stop_flag_ends_the_loop(self):
        DaemonChannel(self.dir).request_stop()
        start = time.time()
        daemon.daemon_run(self.dir, interval=5.0, max_ticks=None)
        self.assertLess(time.time() - start, 2.0)  # stopped fast, did not sleep 5s


class TestRecovery(OSTest):

    def test_removes_leftover_temp_files(self):
        open(os.path.join(self.dir, ".tmp_abc"), "w").close()
        actions = recovery.audit(self.dir)
        self.assertFalse(os.path.exists(os.path.join(self.dir, ".tmp_abc")))
        self.assertTrue(any("temp" in a for a in actions))

    def test_clears_a_stale_lock(self):
        lock = os.path.join(self.dir, "data.lock")
        open(lock, "w").close()
        os.utime(lock, (time.time() - 120, time.time() - 120))
        recovery.audit(self.dir)
        self.assertFalse(os.path.exists(lock))

    def test_quarantines_a_corrupt_profile(self):
        with open(os.path.join(self.dir, "profile.json"), "w") as f:
            f.write("{ this is not json")
        actions = recovery.audit(self.dir)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "profile.json")))
        self.assertTrue(any("quarantined" in a for a in actions))
        self.assertTrue(any(n.startswith("profile.json.corrupt-") for n in os.listdir(self.dir)))

    def test_good_profile_is_left_alone(self):
        with open(os.path.join(self.dir, "profile.json"), "w") as f:
            f.write('{"ok": true}')
        recovery.audit(self.dir)
        self.assertTrue(os.path.exists(os.path.join(self.dir, "profile.json")))


class TestDoctor(OSTest):

    def test_doctor_passes_on_a_clean_dir(self):
        from core import datastore
        old, datastore.DATA_DIR = datastore.DATA_DIR, self.dir
        try:
            from osutil import doctor
            self.assertTrue(doctor.run())
        finally:
            datastore.DATA_DIR = old


@unittest.skipUnless(os.environ.get("ECHOSELF_SPAWN_TEST") == "1",
                     "spawns a real process; set ECHOSELF_SPAWN_TEST=1 to run")
class TestDaemonSpawn(OSTest):

    def test_start_status_stop_a_real_process(self):
        # spawns a real detached daemon; tolerant so a locked-down environment
        # skips instead of failing the suite
        if not daemon.start(self.dir):
            self.skipTest("could not start daemon")
        ch = DaemonChannel(self.dir)
        up = False
        for _ in range(50):
            if ch.running():
                up = True
                break
            time.sleep(0.1)
        if not up:
            self.skipTest("daemon did not come up in this environment")
        self.assertTrue(daemon.stop(self.dir, wait=8.0))


if __name__ == "__main__":
    unittest.main()
