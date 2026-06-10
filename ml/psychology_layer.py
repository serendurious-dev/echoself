"""the response engine. reads the detected state, decides who the character is today.

    Flowing  -> Challenger   harder questions, faster pace, playful pressure
    Pushing  -> Companion    empathy first, new angle, slower, zero judgment
    Drifting -> Presence     soft lesson, no pressure, Drift Mode offered
    Avoiding -> Mirror       gentle confrontation: "you've been circling this one.
                             want to try it once?"
    Fading   -> Memory       shows the user their own past wins, in the character's
                             voice. the evidence is already in the log, we just
                             show it back.

not a mood tracker. it decides, without asking, whether you need to be challenged
or held. also emits the per-session drift nudge for personality_drift.py.
"""

# Layer 2
