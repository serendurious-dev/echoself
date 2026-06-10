"""Psychology layer — the response engine.

Reads the ML brain's detected state and decides the character's mode for the
session. Not a mood tracker: a behavioral intelligence that determines,
without asking, whether the user needs to be challenged or held.

    Detected state -> Character mode
    Flowing        -> Challenger  (harder questions, faster pace, playful pressure)
    Pushing        -> Companion   (empathy first, new explanation angle, slower)
    Drifting       -> Presence    (soft lesson, no pressure, Drift Mode offered)
    Avoiding       -> Mirror      (gentle confrontation: "You've been circling
                                   this one. Want to try it once?")
    Fading         -> Memory      (surfaces the user's own past wins, in the
                                   character's voice — the system already has
                                   the evidence; it just shows it back)

Also emits the per-session drift nudge consumed by
character/personality_drift.py.
"""

# Implementation arrives in Layer 2.
