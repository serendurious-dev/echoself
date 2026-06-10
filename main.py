"""EchoSelf — entry point.

"The version of you that made it — is waiting to tell you how."

Usage:
    python main.py              # normal session
    python main.py --demo      # lived-in profile: ~35 days of synthetic history
    python main.py --timelapse # accelerated mode: each session counts as one day
"""

import argparse
import sys

__version__ = "0.1.0-layer0"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="echoself",
        description="A living psychological companion and adaptive learning system.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="experience EchoSelf with a lived-in profile (~35 days of synthetic history)",
    )
    parser.add_argument(
        "--timelapse",
        action="store_true",
        help="accelerated mode: each session counts as one full day",
    )
    parser.add_argument("--version", action="version", version=f"EchoSelf {__version__}")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    print()
    print("  EchoSelf")
    print('  "The version of you that made it — is waiting to tell you how."')
    print()
    print(f"  This is the project foundation (v{__version__}).")
    print("  The worlds are not awake yet — the engine arrives in Layer 1.")
    if args.demo:
        print("  (--demo noted: the seeded lived-in profile ships with the demo system.)")
    if args.timelapse:
        print("  (--timelapse noted: accelerated days ship with the demo system.)")
    print()
    print("  Follow the build: see README.md and the open issues.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
