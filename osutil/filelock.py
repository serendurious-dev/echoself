"""a cross-process file lock on O_CREAT | O_EXCL, with stale-lock reclaim."""

import os
import time


class FileLock:

    def __init__(self, target, timeout=10.0, poll=0.05, stale=30.0):
        self.path    = str(target) + ".lock"
        self.timeout = timeout
        self.poll    = poll
        self.stale   = stale
        self._fd     = None

    def acquire(self):
        start = time.time()
        while True:
            try:
                self._fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(self._fd, f"{os.getpid()} {time.time():.0f}".encode())
                return self
            except FileExistsError:
                self._steal_if_stale()
                if time.time() - start >= self.timeout:
                    raise TimeoutError(f"timed out acquiring lock: {self.path}")
                time.sleep(self.poll)
            except PermissionError:
                # windows quirk mid-race - same meaning, just retry
                if time.time() - start >= self.timeout:
                    raise TimeoutError(f"timed out acquiring lock: {self.path}")
                time.sleep(self.poll)

    def _steal_if_stale(self):
        # reclaim a lock whose holder died and never released it
        try:
            if time.time() - os.path.getmtime(self.path) > self.stale:
                os.remove(self.path)
        except (FileNotFoundError, PermissionError):
            pass

    def release(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        for _ in range(50):
            try:
                os.remove(self.path)
                return
            except FileNotFoundError:
                return
            except PermissionError:
                time.sleep(0.01)   # windows: file handle not yet free, retry

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *exc):
        self.release()
