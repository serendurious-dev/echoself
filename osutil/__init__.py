"""the OS layer: file locking, the companion daemon, IPC, crash recovery. stdlib only."""

from osutil.filelock import FileLock
from osutil.ipc import DaemonChannel

__all__ = ["FileLock", "DaemonChannel"]
