"""when she reaches out, and what she says.

once a day, in the user's own waking hours, and only on a day they haven't already
come by - a companion checks in, it doesn't nag. the words fit the time of day;
they lean gentle when things have been heavy; and, only if the user asked for the
proactive style, they lean on what she remembers (the portrait). all offline, all
read from the user's own local clock - never an assumption about when "day" is."""

import random

from core import timeofday, settings, session_manager, companion, portrait

_HEAVY      = ("sadness", "anger", "fear", "loneliness", "shame")
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
    # weave the user's name in, when she knows it - a notification that says your
    # name lands differently than one that doesn't
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
