"""personality drift: bounded axes nudged each session toward what works. silent."""

from core import datastore

USER_MODEL = "user_model.json"
# five axes now: how hard she pushes, how warm she is, how fast she moves, how
# playful she lets herself be, and how forward she is about reaching toward you.
AXES       = ("challenge", "warmth", "pace", "humor", "openness")

# how each detected state moves each axis, per session. small on purpose -
# thirty sessions should change someone, one session should not.
_NUDGES = {
    "Flowing":  dict(challenge=+0.04, warmth=-0.01, pace=+0.03, humor=+0.03, openness=+0.02),
    "Pushing":  dict(challenge=-0.03, warmth=+0.04, pace=-0.02, humor=-0.01, openness=+0.01),
    "Drifting": dict(challenge=-0.01, warmth=+0.02, pace=-0.04, humor=-0.02, openness=-0.01),
    "Avoiding": dict(challenge=+0.02, warmth=+0.02, pace=0.0,   humor=-0.01, openness=+0.03),
    "Fading":   dict(challenge=-0.04, warmth=+0.06, pace=-0.04, humor=-0.03, openness=+0.02),
}


def load():
    model = datastore.load_json(USER_MODEL, default={}) or {}
    drift = model.get("drift", {})
    return {axis: float(drift.get(axis, 0.0)) for axis in AXES}


def save(drift):
    model = datastore.load_json(USER_MODEL, default={}) or {}
    model["drift"] = {axis: round(drift.get(axis, 0.0), 4) for axis in AXES}
    datastore.save_json(USER_MODEL, model)


# how a conversation's emotion moves the axes - smaller than the session nudge,
# so it takes a season of talks to shift her, not one sentence.
_EMOTION_NUDGES = {
    "sadness":    dict(warmth=+0.02, pace=-0.02, challenge=-0.01, humor=-0.02),
    "fear":       dict(warmth=+0.02, pace=-0.02, humor=-0.015),
    "loneliness": dict(warmth=+0.03, openness=+0.02),
    "shame":      dict(warmth=+0.03, challenge=-0.02, humor=-0.02),
    "anger":      dict(warmth=+0.015, challenge=-0.015),
    "grief":      dict(warmth=+0.03, pace=-0.03, humor=-0.03),
    "overwhelm":  dict(warmth=+0.02, pace=-0.02, humor=-0.01),
    "numbness":   dict(warmth=+0.02, openness=+0.01, humor=-0.01),
    "joy":        dict(challenge=+0.02, warmth=-0.005, humor=+0.03),
}


def nudge(drift, state):
    # .get so a partial drift dict (an older save, a test) never raises
    for axis, amount in _NUDGES.get(state, {}).items():
        drift[axis] = max(-1.0, min(1.0, drift.get(axis, 0.0) + amount))
    return drift


def nudge_emotion(drift, emotion):
    # the character learns you from how you talk, not just how you study
    for axis, amount in _EMOTION_NUDGES.get(emotion, {}).items():
        drift[axis] = max(-1.0, min(1.0, drift.get(axis, 0.0) + amount))
    return drift


# -- what the drift actually changes ------------------------------------------
# timing, tone, and playfulness on the good days.

def pace_hesitation(drift, base_s):
    # warm-drifted characters wait longer before noticing, challenge-drifted
    # ones expect you to move - the same fourteen seconds stops being fourteen
    return base_s * (1.0 + drift.get("warmth", 0.0) * 0.45 - drift.get("challenge", 0.0) * 0.25)


def prefers_warmth(drift):
    return drift.get("warmth", 0.0) >= 0.3


def prefers_humor(drift):
    # she only lets the lightness out once she's drifted playful enough for it
    return drift.get("humor", 0.0) >= 0.3
