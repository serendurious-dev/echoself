"""a motivational-interviewing stance, for when someone's stuck between wanting to
change and not wanting to.

MI doesn't push or advise - it reflects what it hears, affirms the wanting, asks
one open question, and leaves the choice firmly with the person. detection here is
deliberately light (explicit ambivalence cues only); the richer read is the
model's job when it's on. (Miller & Rollnick, Motivational Interviewing.)"""

import random

# explicit 'i want to but...' style cues - the spoken shape of ambivalence
_CUES = ["i want to but", "i should but", "i know i should", "i keep meaning to",
         "i can't seem to", "i keep trying", "part of me wants", "i don't know if i can",
         "i need to but", "i keep telling myself", "i should probably", "i wish i could but"]

# reflections in the MI spirit: name both sides, affirm, ask open, support autonomy
_REFLECTIONS = [
    "sounds like part of you really wants this and part of you isn't sure - and both of those "
    "get to be true at the same time.",
    "you keep coming back to it, which tells me it matters to you. if you did want to move, what "
    "would the smallest step even look like?",
    "it's not that you don't care - it sounds like you care and it's genuinely hard. what's the "
    "part that's hardest?",
    "you get to decide if and when - no push from me. when you picture actually doing it, what "
    "comes up?",
    "i hear the wanting and the weight, both. which one feels louder today?",
]


def is_ambivalent(text):
    t = text.lower()
    return any(c in t for c in _CUES)


def reflect():
    return random.choice(_REFLECTIONS)
