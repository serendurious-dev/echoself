"""data primitives: the data/ dir, atomic json, csv append and read.

everything the user generates goes through here and only here. local files,
gitignored, never transmitted - see SECURITY.md. json writes are atomic
(write temp -> fsync -> replace), a crash leaves the old file or the new
one, never a half-written one. csv logs are append-only by design, history
does not get rewritten.
"""

import os
import csv
import json
import tempfile

from osutil import FileLock

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def data_path(name):
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, name)


def _lock():
    # one lock for the whole data dir. the app and the companion daemon both
    # take it before writing, so a write is never half-seen or lost. reads stay
    # lock-free - atomic writes mean a reader sees the old file or the new one,
    # never a torn one.
    return FileLock(data_path(".data"))


def atomic_write_text(path, text):
    # write -> fsync -> rename. crash anywhere = old file survives.
    directory = os.path.dirname(os.path.abspath(path))
    fd, temp = tempfile.mkstemp(dir=directory, prefix=".tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.remove(temp)
        except OSError:
            pass
        raise


def save_json(name, obj):
    with _lock():
        atomic_write_text(data_path(name), json.dumps(obj, indent=2, ensure_ascii=False))


def load_json(name, default=None):
    try:
        with open(data_path(name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def append_csv(name, fieldnames, row):
    # first write brings the header with it, after that rows just append
    path = data_path(name)
    with _lock():
        is_new = not os.path.exists(path)
        with open(path, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if is_new:
                writer.writeheader()
            writer.writerow(row)


def read_csv(name):
    try:
        with open(data_path(name), encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    except OSError:
        return []
