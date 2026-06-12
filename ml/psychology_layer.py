"""state -> character mode, and the session plan the lesson acts on. drives the drift."""

from learning import progress_tracker
from character import personality_drift

# per state: resting expression, the phrase slot that opens the session,
# and the hesitation window before the character gently notices (seconds)
_PLANS = {
    "Flowing":  dict(mode="Challenger", expression="happy",    opening_slot="greeting",      hesitation_s=22.0),
    "Pushing":  dict(mode="Companion",  expression="patient",  opening_slot="encouragement", hesitation_s=9.0),
    "Drifting": dict(mode="Presence",   expression="drift",    opening_slot="greeting",      hesitation_s=18.0),
    "Avoiding": dict(mode="Mirror",     expression="thinking", opening_slot="encouragement", hesitation_s=14.0),
    "Fading":   dict(mode="Memory",     expression="patient",  opening_slot="encouragement", hesitation_s=12.0),
}


def _memory_line(track="python"):
    # the Memory mode's whole trick: their own history, said back to them
    done = sorted(progress_tracker.completed_lessons(track))
    if done:
        return f"last time, you finished {len(done)} lesson{'s' if len(done) != 1 else ''}. that happened. it was you."
    rows = [r for r in progress_tracker.read_learning_log() if r["correct"] == "yes"]
    if rows:
        return "you have gotten things right here before. the log remembers, even when you don't."
    return "you came back. that is already the hard part."


def plan_for(state, track="python"):
    # the session plan: what the lesson engine needs to act on the state.
    # drift personalizes the plan, then gets nudged by today's state - the
    # slow becoming is two lines of code, applied every single session.
    plan = dict(_PLANS.get(state, _PLANS["Drifting"]))
    plan["state"] = state

    drift = personality_drift.load()
    plan["hesitation_s"] = personality_drift.pace_hesitation(drift, plan["hesitation_s"])
    if personality_drift.prefers_warmth(drift) and plan["opening_slot"] == "greeting":
        plan["opening_slot"] = "encouragement"

    if state == "Fading":
        plan["memory_line"] = _memory_line(track)
    if state == "Avoiding":
        plan["mirror_line"] = "you've been circling this one. want to try it once?"
    if state == "Drifting":
        plan["offer_drift"] = True

    personality_drift.nudge(drift, state)
    personality_drift.save(drift)
    return plan
