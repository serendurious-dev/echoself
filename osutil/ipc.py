"""file-based IPC between the app and the companion daemon. no sockets.

three little files in the data dir do all the talking. the daemon writes its
pid when it starts and a heartbeat every tick; the app reads them to know if
the companion is alive. the app writes a stop-flag; the daemon polls it and
exits cleanly when it appears. that is the whole protocol - plain files, which
is the most portable IPC there is.
"""

import os
import time


class DaemonChannel:

    def __init__(self, data_dir):
        os.makedirs(data_dir, exist_ok=True)
        self.pid_path  = os.path.join(data_dir, "daemon.pid")
        self.beat_path = os.path.join(data_dir, "daemon.beat")
        self.stop_path = os.path.join(data_dir, "daemon.stop")

    @staticmethod
    def _read(path):
        try:
            with open(path, encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            return None

    @staticmethod
    def _write(path, text):
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(text))

    # pid ---------------------------------------------------------------------

    def write_pid(self):
        self._write(self.pid_path, os.getpid())

    def read_pid(self):
        raw = self._read(self.pid_path)
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def clear_pid(self):
        # only the pid - the heartbeat is left behind as a "last seen" stamp,
        # which is harmless (running() also needs the pid) and useful for status
        try:
            os.remove(self.pid_path)
        except OSError:
            pass

    # heartbeat ---------------------------------------------------------------

    def beat(self):
        self._write(self.beat_path, f"{time.time():.0f}")

    def last_beat(self):
        raw = self._read(self.beat_path)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    def is_alive(self, max_age=90.0):
        beat = self.last_beat()
        return beat is not None and (time.time() - beat) <= max_age

    def running(self):
        return self.read_pid() is not None and self.is_alive()

    # stop flag ---------------------------------------------------------------

    def request_stop(self):
        self._write(self.stop_path, "1")

    def stop_requested(self):
        return os.path.exists(self.stop_path)

    def clear_stop(self):
        try:
            os.remove(self.stop_path)
        except OSError:
            pass
