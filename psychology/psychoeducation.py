"""short, plain explanations of what a feeling is doing - and that it passes.

not diagnosis, not treatment: a normalizing word, the kind a calm friend who
happens to know a little might offer. each is one or two sentences, sourced to
well-established public psychology, kept gentle on purpose. she reaches for one
in the acute moments, when understanding what's happening takes some of its power
away. crisis is handled elsewhere and never comes here."""

# emotion -> {line (what she says), source}
_NOTES = {
    "fear": {
        "line": "what you're feeling is your body's alarm system firing - the racing heart, "
                "the fast breath - trying to protect you. it isn't danger, and it physically "
                "can't hold this peak; it always comes back down.",
        "source": "fight-or-flight response (Cannon, 1915); panic psychoeducation in CBT.",
    },
    "overwhelm": {
        "line": "overwhelm is just too many things hitting your working memory at once - it's a "
                "load problem, not a you problem. it eases the second one thing gets set down.",
        "source": "cognitive load theory (Sweller); CBT psychoeducation.",
    },
    "sadness": {
        "line": "low mood drags everything down and swears it's permanent - that's the feeling "
                "talking, not the truth. it lifts, especially with a little movement and a little "
                "kindness.",
        "source": "CBT model of depression (Beck); behavioural activation.",
    },
    "anger": {
        "line": "anger is usually standing guard over something softer underneath - a hurt, a line "
                "crossed. the surge itself is chemical and brief; it peaks in seconds and fades if "
                "you don't keep feeding it.",
        "source": "emotion regulation; the physiology of the anger response.",
    },
    "shame": {
        "line": "shame says 'you are bad,' not 'you did a bad thing' - that swap is the whole trick "
                "of it. it shrinks when it's spoken out loud and met with warmth instead of more "
                "blame.",
        "source": "shame vs guilt (Brown); self-compassion (Neff, 2003).",
    },
    "grief": {
        "line": "grief comes in waves, not a straight line - it's love with nowhere to go. the "
                "waves space out over time, but there's no clock on it and no wrong way to do it.",
        "source": "grief is not linear; the dual-process model (Stroebe & Schut).",
    },
    "loneliness": {
        "line": "loneliness is a signal, like hunger - it's your wiring asking for connection, not "
                "proof that you're unwanted or that something's wrong with you.",
        "source": "loneliness as a biological signal (Cacioppo).",
    },
    "numbness": {
        "line": "going numb is often the mind protecting you from too much at once - a circuit "
                "breaker, not a broken part. the feeling comes back, gently, when it's safe to.",
        "source": "emotional numbing as protective; common in stress responses.",
    },
}


def line(emotion):
    note = _NOTES.get(emotion)
    return note["line"] if note else None


def explain(emotion):
    return _NOTES.get(emotion)
