"""the session spine: the profile, and the one-word one-number mood log."""

import datetime

from core import datastore

PROFILE_FILE = "profile.json"
ECHO_LOG     = "echo_log.csv"
ECHO_FIELDS  = ["date", "time", "mood_word", "mood_score",
                "mental", "behavioral", "emotional", "learning"]


def load_profile():
    # None on first run. callers decide what first run means, not this module.
    return datastore.load_json(PROFILE_FILE)


def save_profile(profile):
    datastore.save_json(PROFILE_FILE, profile)


def log_mood(word, score, when=None, distances=None):
    # one word, one number, minimal friction. distances arrive with the brain.
    when = when or datetime.datetime.now()
    d    = distances or {}
    datastore.append_csv(ECHO_LOG, ECHO_FIELDS, {
        "date":       when.strftime("%Y-%m-%d"),
        "time":       when.strftime("%H:%M"),
        "mood_word":  word,
        "mood_score": int(score),
        "mental":     d.get("mental", ""),
        "behavioral": d.get("behavioral", ""),
        "emotional":  d.get("emotional", ""),
        "learning":   d.get("learning", ""),
    })


def read_echo_log():
    return datastore.read_csv(ECHO_LOG)


def recent_entries(days):
    # everything from the last n days, oldest first. the Dark Days check and
    # the 30-day timeline both read through this.
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    return [row for row in read_echo_log() if row["date"] >= cutoff]


def logged_today():
    today = datetime.date.today().isoformat()
    return any(row["date"] == today for row in read_echo_log())
