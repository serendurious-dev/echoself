"""the knowledge base behind the companion's support.

named, sourced wellbeing frameworks, encoded as data she can offer - gently, and
only if you say yes - when a feeling calls for more than presence. these are
everyday coping tools drawn from well-established public approaches, not therapy
and not treatment: EchoSelf is a companion, not a clinician. crisis always
overrides all of this (see core/companion). sources are listed in ETHICS.md."""

# each framework: who it's for, where it comes from, the gentle offer line (a
# question - she never starts a technique without a yes), and the walk itself.
FRAMEWORKS = {
    "grounding_54321": {
        "name":   "5-4-3-2-1 grounding",
        "for":    "panic, a spiralling mind",
        "source": "University of Rochester Medical Center, Behavioral Health Partners (2018).",
        "offer":  "your body's in alarm mode right now. want to do one tiny grounding thing with me? just say yes.",
        "walk": (
            "okay. slow, with me - out loud or in your head:\n"
            "five things you can see. name them, one at a time.\n"
            "four things you can feel - the chair, your feet, your sleeves.\n"
            "three things you can hear.\n"
            "two things you can smell.\n"
            "one thing you can taste.\n"
            "that's it. you pulled yourself back to right now. how's the air feel?"),
    },
    "paced_breathing": {
        "name":   "paced breathing",
        "for":    "the hot rush of stress or anger",
        "source": "Paced / diaphragmatic breathing, widely used in CBT and DBT.",
        "offer":  "want to slow the breath down together, just a few rounds? say yes if you do.",
        "walk": (
            "with me, no rush:\n"
            "in through the nose, slow - one, two, three, four.\n"
            "hold it soft - two, three, four.\n"
            "out through the mouth, longer - one, two, three, four, five, six.\n"
            "again, a few times. the long exhale is the part that tells your body it's safe.\n"
            "i'm right here while you do it."),
    },
    "self_compassion": {
        "name":   "self-compassion",
        "for":    "shame and the harsh inner voice",
        "source": "Neff, K. (2003). Self-Compassion. Self and Identity, 2(2), 85-101.",
        "offer":  "can i offer you one gentle thing, instead of the voice that's beating you up? just say yes.",
        "walk": (
            "three small truths, then i'll let them sit:\n"
            "one - this hurts, and it's okay to say it hurts. don't push it away.\n"
            "two - you're not the only one. everyone fails and falls short; it's the price of "
            "being a person, not proof you're broken.\n"
            "three - talk to yourself the way you'd talk to someone you love who did the exact "
            "same thing. you'd be kind to them. you're allowed that too.\n"
            "that's all. be a little on your own side."),
    },
    "cbt_reframe": {
        "name":   "a gentle reframe",
        "for":    "catastrophising, all-or-nothing, mind-reading",
        "source": "Cognitive behavioural therapy (Beck); cognitive distortions, simplypsychology.org.",
        "offer":  "want to look at that thought together for a second - not to argue with you, just to check it? say yes if you do.",
        "walk": (
            "okay, gently. a scared mind does three sneaky things:\n"
            "it jumps to the worst case (catastrophising).\n"
            "it goes all-or-nothing - one slip and it's 'total failure'.\n"
            "it reads minds - you 'know' what they think of you, but you don't, not really.\n"
            "is the thought that's hurting maybe one of those? what would the fairer, calmer "
            "version of it sound like?"),
    },
    "kaizen_step": {
        "name":   "one small step",
        "for":    "overwhelm and the freeze that comes with it",
        "source": "Kaizen - change by tiny steps; echoes EchoSelf's presence-over-pressure.",
        "offer":  "it's too big to hold all at once. want to shrink it down to one step with me? say yes.",
        "walk": (
            "we're not solving the whole thing. just the next inch:\n"
            "what's the smallest possible piece - so small it's almost silly - you could do in "
            "the next ten minutes? not the project. one email. one page. one glass of water.\n"
            "do that one. the rest can wait. momentum is built, not summoned."),
    },
    "stoic_control": {
        "name":   "what's yours to hold",
        "for":    "anxiety about what you can't control",
        "source": "Stoic dichotomy of control; Epictetus, Enchiridion.",
        "offer":  "want to sort this into what's yours and what isn't? sometimes that's the whole relief. say yes.",
        "walk": (
            "two piles, honestly:\n"
            "what here is actually in your hands - your effort, your next choice, your words?\n"
            "and what simply isn't - other people, the outcome, the past?\n"
            "pour your care into the first pile. let the second be heavy somewhere you're not "
            "carrying it. you've been holding both, and only one is yours."),
    },
    # DBT distress tolerance - for the acute moments, when a feeling is too big to
    # think your way out of. survival skills, not fixes. (Linehan, DBT.)
    "dbt_tipp": {
        "name":   "TIPP, to bring the panic down fast",
        "for":    "a panic attack, a body in full alarm",
        "source": "Linehan, M. (2015). DBT Skills Training Manual, 2nd ed. - distress tolerance, TIPP.",
        "offer":  "your body's flooded right now, and there's a fast way to bring it down. want to do it with me? just say yes.",
        "walk": (
            "okay - fastest first, cold:\n"
            "if you can, splash cold water on your face, or hold something cold to your cheeks and "
            "around your eyes for thirty seconds. cold on the face slows your heart on purpose - "
            "it's a reflex, not willpower. (skip the cold if your heart isn't well.)\n"
            "then burn some of it off - twenty seconds of something hard: push against a wall, jog "
            "on the spot, clench and release your fists.\n"
            "then the breath: in for four, out slow for six, a few rounds - the long exhale is the "
            "off-switch.\n"
            "your body's screaming danger, but it's wrong - this peaks and then it always comes "
            "down. i'm right here the whole time."),
    },
    "dbt_stop": {
        "name":   "STOP, before the urge wins",
        "for":    "an impulse you might regret - to lash out, to run, to do something to the moment",
        "source": "Linehan, M. (2015). DBT Skills Training Manual, 2nd ed. - distress tolerance, STOP.",
        "offer":  "want a four-step thing to put a gap between the feeling and what you do next? say yes.",
        "walk": (
            "four beats, with me:\n"
            "S - stop. don't move, don't send, don't act. freeze the frame.\n"
            "T - take a step back. one breath, drop your shoulders.\n"
            "O - observe. just the facts of what's happening, not the story about it.\n"
            "P - proceed mindfully. now pick the move the calmer you would pick.\n"
            "the urge passes faster than it swears it will."),
    },
    "dbt_radical_acceptance": {
        "name":   "radical acceptance",
        "for":    "pain you can't change right now",
        "source": "Linehan, M. (2015). DBT Skills Training Manual, 2nd ed. - distress tolerance, radical acceptance.",
        "offer":  "this might be one you can't fix tonight, only carry. want a gentler way to carry it? say yes.",
        "walk": (
            "accepting isn't agreeing, and it isn't giving up - it's stopping the second fight, "
            "the one against the fact that it happened.\n"
            "say it once, plainly: this is how it is right now. i don't like it, and it's real.\n"
            "notice where you tense up to argue with reality, and let just that part soften. the "
            "pain stays; the exhausting war with it doesn't have to. you're allowed to set the war "
            "down and still hurt."),
    },
    "dbt_self_soothe": {
        "name":   "self-soothe, five senses",
        "for":    "raw, frayed, numb - too much or too little feeling at once",
        "source": "Linehan, M. (2015). DBT Skills Training Manual, 2nd ed. - distress tolerance, self-soothe.",
        "offer":  "want to be kind to your senses for one minute - it really does settle the body. say yes.",
        "walk": (
            "one small kind thing per sense, whatever's near:\n"
            "touch - something soft, a blanket, a warm mug in your hands.\n"
            "sound - one song, or the rain, or just quiet.\n"
            "sight - the sky, a photo you love, a candle.\n"
            "smell - tea, soap, fresh air from a window.\n"
            "taste - something small, slowly.\n"
            "you don't have to earn comfort. give your body one honest minute of it."),
    },
}


def get(key):
    return FRAMEWORKS.get(key)


def offer_line(key):
    fw = FRAMEWORKS.get(key)
    return fw["offer"] if fw else None


def walk(key):
    fw = FRAMEWORKS.get(key)
    return fw["walk"] if fw else None
