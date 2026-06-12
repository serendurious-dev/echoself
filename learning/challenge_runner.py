"""editor-handoff coding: write a starter .py, the user solves it, we run it vs the cases."""

import os
import sys
import json
import subprocess

# overridable for tests, same pattern as datastore.DATA_DIR
WORKSPACE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace")
TIMEOUT_S = 10


def starter_path(challenge):
    os.makedirs(WORKSPACE, exist_ok=True)
    return os.path.join(WORKSPACE, challenge["id"] + ".py")


def write_starter(challenge):
    # write the starter file - but never clobber work already in progress
    path = starter_path(challenge)
    if not os.path.exists(path):
        header = (f"# {challenge['title']}\n"
                  f"# {challenge['prompt']}\n"
                  f"# Solve it here, save, then come back to EchoSelf and run it.\n\n")
        with open(path, "w", encoding="utf-8") as f:
            f.write(header + challenge["starter"])
    return path


def open_in_editor(path):
    # best-effort: open the file in the user's default editor. never fatal.
    try:
        if os.name == "nt":
            os.startfile(path)                                   # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False


def _harness(path, function, cases):
    # a tiny script that imports the user's file and checks every case. it
    # prints PASS, or FAIL with the first case that broke, and exits accordingly.
    return (
        "import importlib.util, json, sys\n"
        f"spec = importlib.util.spec_from_file_location('solution', r'''{path}''')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "try:\n"
        "    spec.loader.exec_module(m)\n"
        "except Exception as e:\n"
        "    print('ERROR your file did not run:', e); sys.exit(2)\n"
        f"fn = getattr(m, '''{function}''', None)\n"
        f"if fn is None:\n"
        f"    print('ERROR no function named {function}'); sys.exit(2)\n"
        f"cases = json.loads(r'''{json.dumps(cases)}''')\n"
        "for c in cases:\n"
        "    try:\n"
        "        got = fn(*c['args'])\n"
        "    except Exception as e:\n"
        "        print('ERROR', c['args'], 'raised', e); sys.exit(1)\n"
        "    if got != c['expect']:\n"
        "        print('FAIL', c['args'], 'gave', repr(got), 'expected', repr(c['expect'])); sys.exit(1)\n"
        "print('PASS')\n"
    )


def run(challenge):
    # execute the user's solution against the cases. returns (passed, detail).
    path = starter_path(challenge)
    if not os.path.exists(path):
        return False, "the starter file isn't there yet - open the challenge first."
    try:
        proc = subprocess.run([sys.executable, "-c",
                               _harness(path, challenge["function"], challenge["cases"])],
                              capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return False, "it ran too long - is there a loop that never ends?"
    out = (proc.stdout or proc.stderr).strip()
    return proc.returncode == 0, out or "no output"
