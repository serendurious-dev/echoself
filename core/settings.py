"""user settings: whether she reaches out, and how. a tiny json the user owns,
sits in the data dir like everything else (so --export and --forget cover it)."""

from core import datastore

SETTINGS_FILE = "settings.json"

# outreach on by default (one keypress to turn off); general is the gentler default.
DEFAULTS = {
    "outreach":       True,         # may she send a daily check-in at all
    "outreach_style": "general",    # "general" | "personal"
    "learning_track": "python",     # which language CodePath is teaching
}

STYLES = ("general", "personal")


def load():
    saved = datastore.load_json(SETTINGS_FILE, default=None)
    out   = dict(DEFAULTS)
    if isinstance(saved, dict):
        for k in DEFAULTS:
            if k in saved:
                out[k] = saved[k]
    return out


def get(key):
    return load().get(key, DEFAULTS.get(key))


def set(key, value):
    cur = load()
    cur[key] = value
    datastore.save_json(SETTINGS_FILE, cur)
    return cur


def toggle_outreach():
    return set("outreach", not get("outreach"))["outreach"]


def toggle_style():
    nxt = "personal" if get("outreach_style") == "general" else "general"
    return set("outreach_style", nxt)["outreach_style"]
