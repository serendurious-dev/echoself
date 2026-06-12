"""your data, your control: export it all to a zip, or forget it entirely."""

import os
import shutil
import zipfile
import datetime

from core import datastore


def export(dest_dir=None):
    # zip everything in the data dir - profile, logs, letters, the vault - so the
    # user can take their data and leave. returns the path to the zip.
    src = datastore.DATA_DIR
    os.makedirs(src, exist_ok=True)
    dest_dir = dest_dir or os.getcwd()
    path = os.path.join(dest_dir, f"echoself_data_{datetime.date.today().isoformat()}.zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(src):
            for name in files:
                full = os.path.join(root, name)
                z.write(full, os.path.relpath(full, src))
    return path


def forget():
    # delete every local file EchoSelf made. nothing kept, nothing phoned home -
    # there was never anywhere for it to go. returns what was removed.
    src = datastore.DATA_DIR
    removed = []
    if os.path.isdir(src):
        for entry in os.listdir(src):
            p = os.path.join(src, entry)
            try:
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
                removed.append(entry)
            except OSError:
                pass
    return removed
