"""the OS layer: file locking, the companion daemon, IPC, crash recovery.

EchoSelf is local-first - no server, no account, no telemetry. that promise is
only real if a single machine can keep one user's data correct while two
processes (the app and a background companion daemon) share the same files.
this package is how: a mutex built on an atomic syscall, file-based IPC, signal
handlers for a clean exit, and a launch audit that cleans up after a crash.

stdlib only. nothing here reaches the network.
"""

from osutil.filelock import FileLock
from osutil.ipc import DaemonChannel

__all__ = ["FileLock", "DaemonChannel"]
