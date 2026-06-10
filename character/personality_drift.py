"""personality drift. the soul of the project, made technical.

three axes, all starting at zero, all bounded to [-1, 1]:

    challenge   how much pressure actually works on this user
    warmth      how much reassurance they need to keep going
    pace        how fast the sessions want to move

every session, the detected state nudges the axes a little toward what is
working - a user who keeps Flowing under challenge drifts the character
toward Challenger, a user who keeps Pushing drifts them toward softness.
nothing is ever announced. after ~30 sessions the numbers have genuinely
moved, and with them the character's patience, their opening words, their
timing. the preset in characters/*.json is never modified - the drift lives
in data/user_model.json, in the space between who they started as and who
you needed.
"""

from core import datastore

USER_MODEL = "user_model.json"
AXES       = ("challenge", "warmth", "pace")

# how each detected state moves each axis, per session. small on purpose -
# thirty sessions should change someone, one session should not.
_NUDGES = {
    "Flowing":  dict(challenge=+0.04, warmth=-0.01, pace=+0.03),
    "Pushing":  dict(challenge=-0.03, warmth=+0.04, pace=-0.02),
    "Drifting": dict(challenge=-0.01, warmth=+0.02, pace=-0.04),
    "Avoiding": dict(challenge=+0.02, warmth=+0.02, pace=0.0),
    "Fading":   dict(challenge=-0.04, warmth=+0.06, pace=-0.04),
}


def load():
    model = datastore.load_json(USER_MODEL, default={}) or {}
    drift = model.get("drift", {})
    return {axis: float(drift.get(axis, 0.0)) for axis in AXES}


def save(drift):
    model = datastore.load_json(USER_MODEL, default={}) or {}
    model["drift"] = {axis: round(drift[axis], 4) for axis in AXES}
    datastore.save_json(USER_MODEL, model)


def nudge(drift, state):
    for axis, amount in _NUDGES.get(state, {}).items():
        drift[axis] = max(-1.0, min(1.0, drift[axis] + amount))
    return drift


# -- what the drift actually changes, today ------------------------------------
# v1 keeps the effects honest and visible: timing and tone. deeper effects
# (phrase rewriting, lesson pacing, expression intensity) are roadmap.

def pace_hesitation(drift, base_s):
    # warm-drifted characters wait longer before noticing, challenge-drifted
    # ones expect you to move - the same fourteen seconds stops being fourteen
    return base_s * (1.0 + drift["warmth"] * 0.45 - drift["challenge"] * 0.25)


def prefers_warmth(drift):
    return drift["warmth"] >= 0.3
