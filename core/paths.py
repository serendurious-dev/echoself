"""where things live, in dev and in a packaged build.

run from source, everything sits in the repo, same as it always did. packaged with
PyInstaller, two things have to move: the bundled read-only assets (lessons, art,
exchange) live in the unpacked bundle, and the user's own data has to go somewhere
that actually persists, not the throwaway bundle dir. this is the one place that
knows the difference."""

import os
import sys


def _repo_root():
    # .../echoself/  (core/paths.py is one level down)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_root():
    # bundled read-only assets: the PyInstaller unpack dir when frozen, else the repo
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return _repo_root()


def data_root():
    # the user's own data, which must survive between runs. a per-user home when
    # packaged, the repo when running from source.
    if getattr(sys, "frozen", False):
        base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"),
                                                          ".local", "share")
        return os.path.join(base, "EchoSelf")
    return _repo_root()
