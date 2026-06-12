"""the 'enough' judgment (from AlterEgo): effort measured against the day's capacity."""

import datetime

from core import session_manager
from learning import progress_tracker

_LINES = {
    "showed_up": "You came on a heavy day. Coming was the hard part, and you did it. That's enough.",
    "capacity":  "You did what today had room for. That is enough - not less, exactly enough.",
    "effort":    "You showed up and you tried. That is a real day. Enough.",
    "not_yet":   "We can leave it here. Rest is part of the work, not a break from it.",
    "absent":    "Whenever you're ready. The door does not close.",
}


def capacity_expected(mood):
    # how much today could fairly ask of you, given the mood (1..10). a heavy
    # day asks for almost nothing; a light day has room for more.
    return max(0, round((mood - 2) / 2.5))


def _today_mood(when):
    day = when.strftime("%Y-%m-%d")
    scores = [int(r["mood_score"]) for r in session_manager.read_echo_log()
              if r["date"] == day and r.get("mood_score")]
    return scores[-1] if scores else None


def session_effort(when):
    # how much actually happened today - lessons, quizzes, challenges
    day = when.strftime("%Y-%m-%d")
    return sum(1 for r in progress_tracker.read_learning_log()
               if r["date"] == day and r["event"] in ("quiz", "lesson_done", "challenge"))


def verdict(profile=None, when=None):
    # the judgment. returns enough (bool), basis (why), and a line to say.
    when   = when or datetime.datetime.now()
    mood   = _today_mood(when)
    effort = session_effort(when)
    showed = mood is not None or effort >= 1

    if not showed:
        basis, enough = "absent", False
    elif mood is not None and mood <= 3:
        basis, enough = "showed_up", True          # a dark day - being here is the whole thing
    elif effort >= capacity_expected(mood if mood is not None else 5):
        basis, enough = "capacity", True            # met what the day allowed
    elif effort >= 1:
        basis, enough = "effort", True
    else:
        basis, enough = "not_yet", False

    return {"enough": enough, "basis": basis, "line": _LINES[basis],
            "mood": mood, "effort": effort}
