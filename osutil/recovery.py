"""crash recovery: clean up after an unclean exit, never lose good data.

run once at launch. it sweeps the data dir for the debris a crash leaves -
leftover temp files from an interrupted atomic write, a lock whose holder died,
a daemon pid with no heartbeat behind it - and it quarantines a corrupt
profile or model file instead of letting the app choke on it. a quarantined
file is moved aside, never deleted, so nothing is ever truly lost.
"""

import os
import time
import json

STALE_LOCK_S = 30.0


def quarantine_if_corrupt(data_dir, name):
    path = os.path.join(data_dir, name)
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            json.load(f)
        return []
    except (ValueError, OSError):
        dest = os.path.join(data_dir, f"{name}.corrupt-{int(time.time())}")
        try:
            os.replace(path, dest)
            return [f"quarantined corrupt {name} (kept as {os.path.basename(dest)})"]
        except OSError:
            return [f"could not quarantine {name}"]


def audit(data_dir):
    # returns a list of what it cleaned up, for logging or the doctor
    actions = []
    if not os.path.isdir(data_dir):
        return actions
    now = time.time()

    for name in os.listdir(data_dir):
        path = os.path.join(data_dir, name)
        if name.startswith(".tmp_"):
            try:
                os.remove(path)
                actions.append(f"removed leftover temp file {name}")
            except OSError:
                pass
        elif name.endswith(".lock"):
            try:
                if now - os.path.getmtime(path) > STALE_LOCK_S:
                    os.remove(path)
                    actions.append(f"cleared stale lock {name}")
            except OSError:
                pass

    from osutil.ipc import DaemonChannel
    channel = DaemonChannel(data_dir)
    if channel.read_pid() is not None and not channel.is_alive():
        channel.clear_pid()
        actions.append("cleared a stale daemon pid (no heartbeat)")

    for name in ("profile.json", "user_model.json"):
        actions += quarantine_if_corrupt(data_dir, name)

    return actions
