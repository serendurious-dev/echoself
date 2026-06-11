"""--doctor: prove the OS layer actually works, in one command.

acquires the lock and confirms a second acquirer is blocked, performs an
atomic write and reads it back, checks the daemon heartbeat channel, and runs
the crash-recovery audit. prints a line per check. this is the one command that
demonstrates the whole systems layer is real and not just described.
"""

import os

from osutil import FileLock
from osutil.ipc import DaemonChannel
from osutil import recovery


def run():
    from core import datastore
    dd = datastore.DATA_DIR
    os.makedirs(dd, exist_ok=True)
    checks = []

    # 1. the lock is a real mutex: a second holder must be blocked
    target = os.path.join(dd, ".doctor")
    held   = FileLock(target, timeout=0.3)
    held.acquire()
    blocked = False
    try:
        FileLock(target, timeout=0.3).acquire()
    except TimeoutError:
        blocked = True
    finally:
        held.release()
    checks.append(("file lock blocks a second holder", blocked))

    # 2. atomic write survives a round trip
    datastore.save_json("doctor_probe.json", {"ok": 1})
    roundtrip = datastore.load_json("doctor_probe.json") == {"ok": 1}
    try:
        os.remove(datastore.data_path("doctor_probe.json"))
    except OSError:
        pass
    checks.append(("atomic write and read back", roundtrip))

    # 3. the daemon heartbeat channel works
    channel = DaemonChannel(dd)
    channel.beat()
    checks.append(("daemon heartbeat read/write", channel.last_beat() is not None))

    # 4. the crash-recovery audit runs clean
    try:
        recovery.audit(dd)
        audit_ok = True
    except Exception:
        audit_ok = False
    checks.append(("crash-recovery audit runs", audit_ok))

    all_ok = all(ok for _, ok in checks)
    print("EchoSelf doctor")
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    print("  all good - the OS layer is sound." if all_ok
          else "  something needs attention.")
    return all_ok
