"""EchoSelf entry point.

python main.py              normal session
python main.py --demo       lived-in profile, ~35 days of history already there
python main.py --timelapse  each session counts as a full day
"""

import argparse
import sys

__version__ = "0.1.0"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="echoself",
        description="A living companion that learns you, teaches you, and grows with you.",
    )
    parser.add_argument("--demo", action="store_true",
                        help="seed a lived-in profile (~35 days of synthetic history)")
    parser.add_argument("--timelapse", action="store_true",
                        help="accelerated mode, each session counts as one day")
    parser.add_argument("--version", action="version", version=f"EchoSelf {__version__}")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # nothing to wake up yet. the worlds arrive with the Layer 1 issues.
    print()
    print("  EchoSelf")
    print('  "The version of you that made it - is waiting to tell you how."')
    print()
    print(f"  v{__version__} - this is the foundation, the worlds are not awake yet.")
    if args.demo:
        print("  (--demo noted, the seeded profile ships with the demo system)")
    if args.timelapse:
        print("  (--timelapse noted, accelerated days ship with the demo system)")
    print()
    print("  Follow the build: README.md and the open issues.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
