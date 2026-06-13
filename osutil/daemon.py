"""the companion daemon: a detached process that beats a heartbeat and leaves a daily note."""

import os
import sys
import time
import signal
import datetime
import subprocess

from osutil.ipc import DaemonChannel


def _presence(data_dir):
    # once a day, leave a single quiet line. the app can surface it; nothing
    # here interrupts the user.
    today  = datetime.date.today().isoformat()
    marker = os.path.join(data_dir, "daemon.lastday")
    try:
        with open(marker, encoding="utf-8") as f:
            if f.read().strip() == today:
                return False
    except OSError:
        pass
    with open(os.path.join(data_dir, "reminders.log"), "a", encoding="utf-8") as f:
        f.write(f"{today}\tI'm still here, whenever you want to come back.\n")
    with open(marker, "w", encoding="utf-8") as f:
        f.write(today)
    return True


def _reach_out(data_dir):
    # the once-a-day check-in - the companion actually speaking, not just beating.
    # the decision (waking hours, not-already-here, opted-in) and the wording live
    # in core.outreach; here we only enforce once-per-day and fire the toast. wrapped
    # whole, because nothing the daemon does to be kind should ever crash it.
    try:
        from core import datastore, outreach, notify
        datastore.DATA_DIR = data_dir
        today  = datetime.date.today().isoformat()
        marker = os.path.join(data_dir, "daemon.reached")
        try:
            with open(marker, encoding="utf-8") as f:
                if f.read().strip() == today:
                    return False
        except OSError:
            pass
        if not outreach.should_reach():
            return False
        notify.notify("EchoSelf", outreach.compose())
        with open(marker, "w", encoding="utf-8") as f:
            f.write(today)
        return True
    except Exception:
        return False


def daemon_run(data_dir, interval=30.0, max_ticks=None, presence=True, outreach=True):
    # the loop. installs signal handlers when it can (only works on the main
    # thread, so tests that call this on a worker just skip them), beats, checks
    # the stop flag, leaves presence, and reaches out once a day. always clears
    # its pid on the way out, so a clean exit never looks like a crash.
    # note: we do NOT clear the stop flag here. start() clears it before
    # spawning, so a stop requested before the loop begins is still honored -
    # otherwise a stop could race a startup and be silently dropped.
    channel = DaemonChannel(data_dir)
    channel.write_pid()

    stop = {"flag": False}

    def _handle(signum, frame):
        stop["flag"] = True

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _handle)
        except (ValueError, OSError):
            pass   # not the main thread (a test) - the stop flag still works

    ticks = 0
    try:
        while not stop["flag"]:
            channel.beat()
            if channel.stop_requested():
                break
            if presence:
                _presence(data_dir)
            if outreach:
                _reach_out(data_dir)
            ticks += 1
            if max_ticks is not None and ticks >= max_ticks:
                break
            slept = 0.0
            while slept < interval and not stop["flag"]:
                if channel.stop_requested():
                    stop["flag"] = True
                    break
                step = min(0.1, interval - slept)
                time.sleep(step)
                slept += step
    finally:
        channel.clear_pid()
        channel.clear_stop()   # never let the flag persist to the next run
    return ticks


def start(data_dir):
    # spawn the daemon detached, so it outlives the app that launched it.
    channel = DaemonChannel(data_dir)
    if channel.running():
        return False
    channel.clear_stop()   # a stale stop from a past session must not kill the new one
    args   = [sys.executable, "-m", "osutil.daemon", "run", "--data", data_dir]
    kwargs = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    if os.name == "nt":
        kwargs["creationflags"] = 0x00000008 | 0x00000200   # DETACHED_PROCESS | NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(args, **kwargs)
    return True


def stop(data_dir, wait=5.0):
    # ask politely with the stop flag, back it with a signal, then confirm
    channel = DaemonChannel(data_dir)
    channel.request_stop()
    pid = channel.read_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except (OSError, ValueError):
            pass
    start_t = time.time()
    while time.time() - start_t < wait:
        if not channel.running():
            channel.clear_stop()
            return True
        time.sleep(0.1)
    channel.clear_stop()
    return not channel.running()


def status(data_dir):
    channel = DaemonChannel(data_dir)
    return {"running": channel.running(),
            "pid": channel.read_pid(),
            "last_beat": channel.last_beat()}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="echoself-daemon")
    parser.add_argument("cmd", choices=["run", "stop", "status"])
    parser.add_argument("--data", required=True)
    a = parser.parse_args()
    if a.cmd == "run":
        daemon_run(a.data)
    elif a.cmd == "stop":
        print("stopped" if stop(a.data) else "was not running")
    else:
        print(status(a.data))
