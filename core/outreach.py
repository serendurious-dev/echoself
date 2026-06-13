"""when she reaches out: once a day, in your waking hours, skipped if you already
came by. the line fits the time of day, softens when things have been heavy, and
leans on the portrait if you chose the proactive style. read from your own clock."""

import random

from core import timeofday, settings, session_manager, companion, portrait

_HEAVY      = ("sadness", "anger", "fear", "loneliness", "shame",
               "overwhelm", "guilt", "grief", "numbness")
_GOOD_PARTS = ("morning", "afternoon", "evening")    # waking hours, not the dead of night

_GENERAL = {
    "morning":   "morning. how are you today?",
    "afternoon": "how's your day going?",
    "evening":   "how was today?",
}


def _recently_heavy(limit=5):
    rows = companion.recent_emotions(limit)
    if not rows:
        return False
    heavy = sum(1 for r in rows if r.get("emotion") in _HEAVY)
    return heavy >= max(2, (len(rows) + 1) // 2)


def _by_name(line):
    # weave the name in when known
    name = (session_manager.load_profile() or {}).get("your_name")
    if name and "?" in line and random.random() < 0.6:
        return line.replace("?", f", {name}?", 1)
    return line


def compose(now=None, style=None):
    # the line she'd send right now. heavy stretch -> the gentlest version;
    # otherwise the chosen style, falling back to a plain check-in.
    if _recently_heavy():
        return _by_name("thinking of you. i'm here whenever you want to talk.")
    style = style or settings.get("outreach_style")
    if style == "personal":
        try:
            hint = portrait.opener_hint(now)
        except Exception:
            hint = None
        if hint:
            return _by_name(f"thinking of you. how's {hint['text']} sitting today?")
    return _by_name(_GENERAL.get(timeofday.daypart(now), "how are you?"))


def should_reach(now=None, already_today=False):
    # the gate. all of these have to be true for her to reach out.
    if not settings.get("outreach"):
        return False
    if already_today:                       # the daemon's once-a-day marker
        return False
    if session_manager.logged_today():      # they already showed up today
        return False
    return timeofday.daypart(now) in _GOOD_PARTS
