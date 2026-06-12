"""--demo seeds a lived-in month into a sandboxed data_demo/; --timelapse adds a day a run."""

import os
import datetime

from core import datastore, session_manager
from learning import progress_tracker

DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_demo")
DAYS     = 35


def use_demo_dir():
    # point all storage at the sandbox. everything downstream reads
    # datastore.DATA_DIR at call time, so this is all it takes.
    datastore.DATA_DIR = DEMO_DIR


def _profile(start):
    return {
        "created":   start.isoformat(),
        "your_name": "friend",
        "ideal_self": {"name": "the steady one", "core_trait": "steadiness",
                       "values": ["honesty", "patience", "courage"]},
        "shadow_self": {"name": "the tired one", "trait": "vanishing"},
        "character": {"pack": "gentle_guide", "build": "female",
                      "hair_style": "long", "skin": "#F2D5C0"},
        "session_zero_signals": [{"hesitation_s": 3.0, "duration_s": 9.0, "length": 8}],
        "demo": True,
    }


def _mood_for(frac):
    # a rough start that dips into a dark stretch, then recovers
    if frac < 0.25:
        base = 6 - 4 * (frac / 0.25)        # 6 -> 2
    elif frac < 0.45:
        base = 2.5                          # the dark days
    else:
        base = 2.5 + 5.5 * ((frac - 0.45) / 0.55)   # 2.5 -> 8
    jitter = (-1, 0, 0, 1)[hash(round(frac, 3)) % 4]
    return max(1, min(10, round(base) + jitter))


def _state_for(frac):
    if frac < 0.45:
        return "Fading" if frac > 0.2 else "Drifting"
    if frac < 0.7:
        return "Pushing"
    return "Flowing"


def seed(days=DAYS, today=None):
    # write a believable month into the (demo) data dir
    today = today or datetime.date.today()
    start = today - datetime.timedelta(days=days - 1)
    session_manager.save_profile(_profile(start))

    lessons = __import__("learning.codepath", fromlist=["load_track"]).load_track("python")
    states  = []
    for i in range(days):
        day  = start + datetime.timedelta(days=i)
        frac = i / max(1, days - 1)
        mood = _mood_for(frac)
        # distances close as the month goes on; emotional tracks the mood
        d = {"mental":     round(max(0.1, 0.8 - 0.5 * frac), 3),
             "behavioral": round(max(0.1, 0.7 - 0.45 * frac), 3),
             "emotional":  round(max(0.1, 1.0 - mood / 10.0), 3),
             "learning":   round(max(0.1, 0.85 - 0.55 * frac), 3)}
        when = datetime.datetime(day.year, day.month, day.day, 20, 0)
        session_manager.log_mood(("heavy" if mood <= 3 else "okay" if mood <= 6 else "lighter"),
                                 mood, when=when, distances=d)
        # some learning on the better days
        if mood >= 5 and lessons:
            idx = min(len(lessons) - 1, i // 8)
            lesson = lessons[idx]
            progress_tracker.log_event("python", lesson["cluster"], lesson["id"], "quiz",
                                       correct="yes" if mood >= 6 else "no",
                                       duration_s=20, when=when)
            if mood >= 6 and i % 8 == 7:
                progress_tracker.log_event("python", lesson["cluster"], lesson["id"],
                                           "lesson_done", when=when)
        states.append({"date": day.isoformat(), "state": _state_for(frac)})

    # a user model that looks drifted-through-a-hard-month: warmer, a little
    # more challenge as it recovered
    datastore.save_json("user_model.json", {
        "last_state": states[-1]["state"],
        "state_history": states[-60:],
        "drift": {"challenge": 0.18, "warmth": 0.42, "pace": -0.05},
    })


def ensure_seeded(days=DAYS, today=None):
    if session_manager.load_profile() is None:
        seed(days, today)


def advance_day():
    # timelapse: tack one more synthetic day onto the demo, dated tomorrow of
    # the latest entry, so the timeline and drift visibly move each launch
    rows = session_manager.read_echo_log()
    if not rows:
        return
    last = datetime.date.fromisoformat(rows[-1]["date"])
    day  = last + datetime.timedelta(days=1)
    mood = _mood_for(1.0)
    d = {"mental": 0.28, "behavioral": 0.26, "emotional": round(1 - mood / 10.0, 3), "learning": 0.30}
    session_manager.log_mood("lighter", mood,
                             when=datetime.datetime(day.year, day.month, day.day, 20, 0),
                             distances=d)
