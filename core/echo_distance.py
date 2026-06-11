"""the four-axis Echo Distance: how far the current self is from the ideal self.

Mental, Behavioral, Emotional, Learning. each is 0..1, where 0 means arrived
and 1 means far. all four are read from what the logs already know - the
brain's recent read of you, whether you have been showing up, your moods, and
how the learning is going - so the gap is measured, never asked.

the original three axes (mental, behavioral, emotional) come from the first
EchoSelf. learning is the fourth axis CodePath added: the gap closes not just
emotionally but intellectually.
"""

from core import session_manager, datastore
from learning import codepath, progress_tracker

AXES = ("mental", "behavioral", "emotional", "learning")

# how good each detected state is for the mental axis (1 = closest)
_STATE_SCORE = {"Flowing": 0.90, "Pushing": 0.60, "Drifting": 0.40,
                "Avoiding": 0.35, "Fading": 0.15}


def _recent_mood_scores(days=14):
    return [int(r["mood_score"]) for r in session_manager.recent_entries(days)
            if r.get("mood_score")]


def compute(profile=None):
    # emotional: recent mood, 1..10. a lighter week closes the gap.
    moods = _recent_mood_scores()
    emotional = 1.0 - (sum(moods) / len(moods) / 10.0) if moods else 0.5

    # learning: how much of the track is done, blended with quiz accuracy.
    # nothing started yet means unknown, not far - no cold-start punishment.
    total    = len(codepath.load_track("python")) or 1
    done     = len(progress_tracker.completed_lessons("python"))
    accuracy = progress_tracker.quiz_accuracy("python")
    if done == 0 and accuracy is None:
        learning = 0.5
    else:
        progress = min(1.0, done / total)
        learning = 1.0 - (0.6 * progress + 0.4 * (accuracy if accuracy is not None else 0.5))

    # behavioral: showing up. active days in the last two weeks, ~every other
    # day is enough to close it. no history yet is unknown, not far.
    active     = len({r["date"] for r in session_manager.recent_entries(14)})
    behavioral = 0.5 if active == 0 else max(0.0, 1.0 - active / 7.0)

    # mental: the brain's recent read of you, averaged over the last week of states
    model = datastore.load_json("user_model.json", default={}) or {}
    states = [h["state"] for h in model.get("state_history", [])][-7:]
    if states:
        mental = 1.0 - sum(_STATE_SCORE.get(s, 0.4) for s in states) / len(states)
    else:
        mental = 0.5

    return {axis: round(max(0.0, min(1.0, value)), 3)
            for axis, value in zip(AXES, (mental, behavioral, emotional, learning))}


def history(days=30):
    # the distance rows already saved in echo_log, oldest first, for the
    # timeline. only rows that actually carry the four numbers.
    rows = []
    for r in session_manager.recent_entries(days):
        if r.get("mental") not in (None, ""):
            rows.append({"date": r["date"],
                         **{axis: float(r[axis]) for axis in AXES}})
    return rows
