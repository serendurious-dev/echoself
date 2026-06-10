"""the daily session spine: the profile, the mood log.

three phases live here eventually: mood capture (one word, one number) ->
pattern check (Dark Days or a normal session) -> save and reflect. this is
the data half - the session flow itself arrives with the narrative engine.

profile.json holds the ideal self, the Shadow Self and the character.
echo_log.csv is one row per mood entry, the four echo distance columns stay
empty until the brain starts filling them in Layer 2.
"""

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
