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
    # --demo and --timelapse are parsed already but they ship with the demo system,
    # nothing for them to seed yet.
    from visual.worlds import run
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
