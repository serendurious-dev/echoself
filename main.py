"""EchoSelf entry point. flags: --demo, --timelapse, --doctor, --daemon, --export, --forget."""

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
    parser.add_argument("--export", action="store_true",
                        help="export all your local data to a zip, and exit")
    parser.add_argument("--forget", action="store_true",
                        help="permanently delete all your local data, and exit")
    parser.add_argument("--serve", nargs="?", const=8765, type=int, default=None,
                        metavar="PORT",
                        help="run the local API server (localhost only) instead of the window")
    parser.add_argument("--desktop", nargs="?", const=8765, type=int, default=None,
                        metavar="PORT",
                        help="open the desktop window: the web UI in a pywebview shell")
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

    if args.export:
        from core import data_control
        print("your data, zipped and yours:", data_control.export())
        return 0

    if args.forget:
        from core import data_control
        print("This permanently deletes all your local EchoSelf data - profile, logs, letters,")
        print("the Vault. It cannot be undone. (Nothing was ever sent anywhere; this is all of it.)")
        if input("Type DELETE to confirm: ").strip() == "DELETE":
            removed = data_control.forget()
            print(f"removed {len(removed)} item(s). nothing kept.")
        else:
            print("cancelled. nothing was touched.")
        return 0

    if args.serve is not None:
        from apiserver import serve
        serve(args.serve)
        return 0

    if args.desktop is not None:
        from desktop import launch
        launch(args.desktop)
        return 0

    from visual.worlds import run
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
