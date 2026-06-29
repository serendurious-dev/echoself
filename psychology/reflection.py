"""reflective listening, offline. the mirror-self idea made literal: before she
answers from a feeling, she mirrors back the thing you actually named - in your own
words, shifted to 'you' the way a listener does - so it lands as 'she heard ME', not
'she picked a category'.

kept deliberately conservative. a wrong reflection is worse than none, so when she
can't find a clear thing to reflect she says nothing extra and the feeling-based
answer carries the turn. (Rogers, client-centred reflection; Miller & Rollnick.)"""

import re
import random

# words too thin to reflect, or that turn a noun into a clause - trimmed off the ends so
# what's left is the thing itself ("your boss never listens" -> "your boss").
_STOP = {"the", "a", "an", "this", "that", "it", "is", "are", "was", "were", "be",
         "been", "really", "just", "so", "very", "much", "more", "lot", "kind", "of",
         "to", "and", "but", "or", "i", "im", "me", "my", "your", "feel", "feeling",
         "like", "right", "now", "today", "thing", "things", "stuff", "again", "still",
         "too", "also",
         # verbs/adverbs/time that trail a topic into a clause
         "never", "always", "ever", "died", "die", "dies", "listens", "listen", "moved",
         "keeps", "keep", "makes", "make", "hurts", "hurt", "hates", "hate", "left",
         "last", "week", "weeks", "month", "months", "year", "years", "ago", "lately",
         "anymore", "tonight", "tomorrow"}

# the most reliable personal-topic signals, tried in order. each captures the noun
# phrase that follows, stopping at punctuation, a clause break, or the end. trailing
# time words ("today", "tonight") count as breaks so they don't trail into the catch.
_BREAK = (r"(?:[.,!?;]| because | and | but | so | is | are | was | were | feels? "
          r"| that | when | who | which | about | today| tonight| tomorrow| lately"
          r"| this | these | all |\s*$)")
_PATTERNS = [
    ("my",    re.compile(r"\bmy ([a-z][a-z' ]{1,28}?)" + _BREAK, re.I)),
    ("about", re.compile(r"\babout ([a-z][a-z' ]{1,28}?)" + _BREAK, re.I)),
    ("cause", re.compile(r"\bbecause (?:of )?([a-z][a-z' ]{1,28}?)" + _BREAK, re.I)),
]

# tentative on purpose - phrased so even a slightly-off catch reads as listening,
# not a confident misread.
_LEADS = [
    "{t} - that's what's sitting with you, isn't it?",
    "sounds like {t} is a lot to hold right now.",
    "so it's {t} that's been weighing on you.",
    "{t} - i hear that.",
    "{t}. that's a real thing to be carrying.",
]


def _clean(phrase):
    # trim filler off both ends, cap the length, and shift 'my'->'your' so she
    # reflects it back the way a listener does. None if there's nothing solid left.
    words = [w for w in re.split(r"\s+", phrase.strip().lower()) if w]
    while words and words[0] in _STOP:
        words.pop(0)
    while words and words[-1] in _STOP:
        words.pop()
    # a clean topic is short. anything longer is probably a whole clause we'd reflect
    # back clumsily - better to say nothing extra than to mirror it wrong.
    if not words or len(words) > 3:
        return None
    return " ".join("your" if w == "my" else w for w in words)


def topic(text):
    # the thing they named, shifted to 'you', or None when nothing clean comes out.
    for kind, pat in _PATTERNS:
        m = pat.search(" " + text + " ")
        if not m:
            continue
        cleaned = _clean(m.group(1))
        if not cleaned:
            continue
        return ("your " + cleaned) if kind == "my" else cleaned
    return None


def lead(t):
    # a short line built around an already-extracted topic.
    return random.choice(_LEADS).format(t=t)


def reflect(text):
    # a short line mirroring what they named, or None to let the feeling answer carry.
    t = topic(text)
    return lead(t) if t else None
