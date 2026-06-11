"""EchoSelf entry point.

python main.py                 normal session
python main.py --demo          lived-in profile, ~35 days of history already there
python main.py --timelapse     each session counts as a full day
python main.py --doctor        prove the OS layer works, then exit
python main.py --daemon start  the companion daemon: start / stop / status
"""

import argparse
import sys

__version__ = "0.2.0"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="echoself",
        description="A living companion that learns you, teaches you, and grows with you.",
    )
    parser.add_argument("--demo", action="store_true",
                        help="seed a lived-in profile (~35 days of synthetic history)")
    parser.add_argument("--timelapse", action="store_true",
                        help="accelerated mode, each session counts as one day")
    parser.add_argument("--doctor", action="store_true",
                        help="run the OS-layer self-diagnostic and exit")
    parser.add_argument("--daemon", choices=["start", "stop", "status"],
                        help="control the companion daemon")
    parser.add_argument("--version", action="version", version=f"EchoSelf {__version__}")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.doctor:
        from osutil import doctor
        return 0 if doctor.run() else 1

    if args.daemon:
        from osutil import daemon
        from core.datastore import DATA_DIR
        if args.daemon == "start":
            print("companion started" if daemon.start(DATA_DIR) else "companion already running")
        elif args.daemon == "stop":
            print("companion stopped" if daemon.stop(DATA_DIR) else "companion was not running")
        else:
            s = daemon.status(DATA_DIR)
            print(f"running={s['running']}  pid={s['pid']}  last_beat={s['last_beat']}")
        return 0

    from visual.worlds import run
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
