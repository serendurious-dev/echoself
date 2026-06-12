"""the ML brain: an sklearn classifier over passive signals -> one of five states."""

import datetime

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from core import datastore, session_manager
from learning import progress_tracker
from ml import archetypes

USER_MODEL = "user_model.json"


def session_features():
    # one feature row per day that had any activity, oldest first
    by_day = {}
    for row in progress_tracker.read_learning_log():
        by_day.setdefault(row["date"], []).append(row)
    for row in session_manager.read_echo_log():
        by_day.setdefault(row["date"], [])

    days = sorted(by_day)
    rows = []
    prev = None
    for day in days:
        events  = by_day[day]
        quizzes = [e for e in events if e.get("event") == "quiz"]
        lessons = [e for e in events if e.get("event") == "lesson_done"]
        hints   = [e for e in events if e.get("event") == "hint"]
        gap     = 0.0
        if prev is not None:
            gap = (datetime.date.fromisoformat(day) - datetime.date.fromisoformat(prev)).days
        accuracy = (sum(1 for q in quizzes if q["correct"] == "yes") / len(quizzes)) if quizzes else 0.6
        duration = (sum(float(q["duration_s"] or 0) for q in quizzes) / len(quizzes)) if quizzes else 25.0
        rows.append([accuracy, duration,
                     (len(hints) / len(quizzes)) if quizzes else 0.0,
                     float(len(events)), float(len(lessons)), float(gap)])
        prev = day
    return rows


def _state_from_session_zero(profile):
    # before any real session exists, the only behavior we have is how they
    # answered the first questions. slow and short suggests low energy, quick
    # and full suggests there is fuel. a soft guess, replaced by real data fast.
    signals = (profile or {}).get("session_zero_signals", [])
    if not signals:
        return "Drifting"
    hesitation = sum(s.get("hesitation_s", 3) for s in signals) / len(signals)
    length     = sum(s.get("length", 8) for s in signals) / len(signals)
    if hesitation > 8.0 and length < 6:
        return "Drifting"
    if hesitation < 2.5 and length >= 10:
        return "Flowing"
    return "Pushing"


def wake():
    # called once at launch. classifies the most recent session, remembers it,
    # returns the state for the psychology layer to act on.
    history = session_features()

    if not history:
        state = _state_from_session_zero(session_manager.load_profile())
    else:
        rows, labels = archetypes.synthetic_sessions()
        weights = [1.0] * len(rows)
        # the user's own past, taught by the heuristic, counts three times as
        # much as any archetype - this is where it becomes about them
        for row in history[:-1]:
            rows.append(row)
            labels.append(archetypes.heuristic_label(row))
            weights.append(3.0)
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        clf.fit(rows, labels, logisticregression__sample_weight=weights)
        state = clf.predict([history[-1]])[0]

    model = datastore.load_json(USER_MODEL, default={}) or {}
    today = datetime.date.today().isoformat()
    hist  = model.get("state_history", [])
    if not hist or hist[-1]["date"] != today:
        hist.append({"date": today, "state": state})
    else:
        hist[-1]["state"] = state
    model["last_state"]    = state
    model["state_history"] = hist[-60:]
    datastore.save_json(USER_MODEL, model)
    return state
