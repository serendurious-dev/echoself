"""read emotion from how someone writes - sad, angry, anxious, lonely, ashamed,
joyful - without ever asking. lexicon-based and offline; the LLM layer can
refine this later, but the floor works with no network.

v1.5 deepens the read past a flat word list: words carry weight (devastated hits
harder than down), intensifiers and hedges scale them (so anxious vs a bit
anxious), negation reaches back across a clause and stops at 'but', and analyze()
exposes a second feeling and a confidence so the rest of the app can tell a clear
mood from a muddled one. detect() keeps its old shape so nothing downstream breaks."""

import re

EMOTIONS = ["joy", "sadness", "anger", "fear", "loneliness", "shame",
            "overwhelm", "guilt", "grief", "numbness"]

# small but real word lists. not exhaustive - the point is to read the drift of
# a message, not to diagnose it.
_LEX = {
    "joy":        ["happy", "glad", "great", "good", "excited", "wonderful", "amazing",
                   "grateful", "relieved", "proud", "content", "calm", "peaceful", "hopeful",
                   "fun", "joy", "joyful", "smiling", "better", "lighter", "okay", "fine",
                   "love", "loved", "enjoyed", "enjoy", "nice", "lovely", "laughed", "won"],
    "sadness":    ["sad", "down", "low", "unhappy", "depressed", "empty", "hopeless", "crying",
                   "cry", "exhausted", "drained", "hurt", "miserable", "heavy", "numb", "lost",
                   "disappointed", "tired", "defeated", "rough", "awful", "terrible", "horrible",
                   "sucks", "bummed", "gloomy", "devastated", "crushed", "broken"],
    "anger":      ["angry", "mad", "furious", "annoyed", "irritated", "frustrated", "rage",
                   "hate", "resent", "unfair", "fed", "sick", "pissed", "livid"],
    "fear":       ["anxious", "afraid", "scared", "worried", "nervous", "panic", "panicking",
                   "stressed", "overwhelmed", "terrified", "uneasy", "dread", "fear", "tense",
                   "dreading", "anxiety"],
    "loneliness": ["alone", "lonely", "isolated", "ignored", "unseen", "nobody", "abandoned",
                   "invisible", "disconnected"],
    "shame":      ["ashamed", "embarrassed", "worthless", "stupid", "failure",
                   "useless", "inadequate", "pathetic"],
    # the feelings people live in that the first six missed. trigger words are
    # kept distinct from the six above so reading the original ones never shifts.
    "overwhelm":  ["burnout", "swamped", "drowning", "buried", "frazzled"],
    "guilt":      ["guilty", "guilt", "regret", "remorse"],
    "grief":      ["grieving", "mourning", "bereaved", "heartbroken"],
    "numbness":   ["hollow", "detached", "blank", "flat"],
}

# a few multi-word cues that a single-word scan would miss
_PHRASES = {
    "joy":        ["good day", "great day", "went well", "felt good", "feeling good",
                   "pretty good"],
    "shame":      ["not good enough", "not enough"],
    "loneliness": ["no one", "left out", "by myself", "on my own"],
    "sadness":    ["give up", "giving up", "can't anymore", "what's the point",
                   "bad day", "rough day", "hard day", "long day", "down day"],
    "overwhelm":  ["too much", "can't keep up", "cant keep up", "burnt out", "burned out",
                   "spread too thin", "so much to do", "drowning in"],
    "guilt":      ["my fault", "should have", "shouldn't have", "let them down",
                   "let you down", "let everyone down", "messed up", "blame myself"],
    "grief":      ["miss them", "miss him", "miss her", "passed away", "lost someone",
                   "she's gone", "he's gone", "they're gone"],
    "numbness":   ["feel nothing", "don't feel anything", "dont feel anything",
                   "can't feel", "nothing matters", "feel empty inside"],
}

# some words carry more than others. membership stays in _LEX above; this only
# scales the ones that are clearly heavier or clearly lighter than a plain hit.
_WEIGHT = {
    # heavier
    "devastated": 1.8, "hopeless": 1.8, "miserable": 1.7, "furious": 1.7, "livid": 1.7,
    "terrified": 1.8, "worthless": 1.8, "pathetic": 1.6, "failure": 1.6, "depressed": 1.7,
    "drowning": 1.6, "heartbroken": 1.8, "empty": 1.4, "numb": 1.4, "rage": 1.6,
    "panicking": 1.6, "abandoned": 1.6, "exhausted": 1.3, "drained": 1.3, "hate": 1.5,
    # lighter
    "okay": 0.5, "fine": 0.5, "good": 0.6, "nice": 0.6, "annoyed": 0.7, "irritated": 0.7,
    "tired": 0.7, "uneasy": 0.7, "down": 0.7, "low": 0.7, "rough": 0.7, "bummed": 0.7,
    "calm": 0.6, "content": 0.7, "better": 0.7, "lighter": 0.7,
}

# scale the feeling word that follows them. multi-word hedges land on their last
# token ("a bit" -> "bit", "kind of" reaches back two), so the common ones are here.
_INTENSIFIERS = {"so": 1.5, "very": 1.5, "really": 1.4, "extremely": 1.9, "incredibly": 1.7,
                 "absolutely": 1.7, "completely": 1.6, "totally": 1.5, "deeply": 1.6,
                 "super": 1.5, "too": 1.4, "unbelievably": 1.7, "terribly": 1.6, "utterly": 1.7,
                 "such": 1.3, "damn": 1.5, "fucking": 1.8}
_DIMINISHERS = {"bit": 0.5, "little": 0.6, "slightly": 0.5, "somewhat": 0.6, "kinda": 0.6,
                "kind": 0.6, "sorta": 0.6, "mildly": 0.6, "mostly": 0.8, "abit": 0.5}

# negation stops at the clause boundary - "sad but okay" shouldn't negate sad.
_CLAUSE_BREAKS = {"but", "however", "though", "although", "yet", "still"}

_NEGATIONS = {"not", "no", "never", "isnt", "isn't", "wasnt", "wasn't", "dont", "don't",
              "didnt", "didn't", "cant", "can't", "wont", "won't", "arent", "aren't",
              "hardly", "barely", "aint", "ain't"}

# crisis phrases, handled before anything else (see companion.py). err toward
# catching: a missed one is far worse than a false alarm.
_CRISIS = ["kill myself", "killing myself", "end my life", "ending my life",
           "end it all", "ending it all", "end it", "suicide", "suicidal",
           "want to die", "wanna die", "don't want to live", "do not want to live",
           "dont want to be here", "don't want to be here", "hurt myself", "harm myself",
           "self harm", "self-harm", "no reason to live", "no point in living",
           "better off dead", "better off without me", "can't go on", "cant go on",
           "can't do this anymore", "cant do this anymore", "can't take it anymore",
           "cant take it anymore", "want it to end", "tired of living", "give up on life"]

# the few words that mean "yes, walk me through it" - read only when she's just
# offered a technique, so a normal "okay" never gets mistaken for one.
_AFFIRM = {"yes", "yeah", "yep", "yup", "sure", "ok", "okay", "please", "alright",
           "lets", "yes please", "go on", "do it", "i guess", "sounds good", "go ahead"}


def is_crisis(text):
    t = text.lower()
    return any(phrase in t for phrase in _CRISIS)


def is_affirmation(text):
    t = text.strip().lower().strip(".!").strip()
    if t in _AFFIRM:
        return True
    return bool(set(re.findall(r"[a-z']+", t)) &
                {"yes", "yeah", "yep", "yup", "sure", "okay", "ok", "please", "alright"})


def _tokens(text):
    return re.findall(r"[a-z']+", text.lower())


def _word_of(tok):
    # which emotion a token belongs to, or None. first match wins, lists are disjoint.
    for emo, words in _LEX.items():
        if tok in words:
            return emo
    return None


def _modifier(toks, i):
    # an intensifier or hedge sitting just before the feeling word scales it. look
    # back two, so both "so anxious" and "a bit anxious" land.
    for j in (i - 1, i - 2):
        if j < 0:
            continue
        if toks[j] in _INTENSIFIERS:
            return _INTENSIFIERS[toks[j]]
        if toks[j] in _DIMINISHERS:
            return _DIMINISHERS[toks[j]]
    return 1.0


def _negated(toks, i):
    # is the feeling word negated? reach back up to three tokens, but stop at a
    # clause break so "down but fine" doesn't read fine as negated.
    for j in range(i - 1, max(-1, i - 4), -1):
        if toks[j] in _CLAUSE_BREAKS:
            return False
        if toks[j] in _NEGATIONS:
            return True
    return False


def _emphasis(text):
    # shouting and exclamation don't say which feeling, only how loud. a small,
    # capped bump on whatever was already detected.
    bump = 1.0
    if text.count("!") >= 2:
        bump += 0.15
    if re.search(r"\b[A-Z]{3,}\b", text):
        bump += 0.15
    return min(bump, 1.3)


def _lexicon_analyze(text):
    # the offline floor: weighted word lists + modifiers + negation. always here,
    # never needs a model or a network.
    low    = text.lower()
    scores = {e: 0.0 for e in EMOTIONS}

    for emo, phrases in _PHRASES.items():
        for p in phrases:
            if p in low:
                scores[emo] += 1.5

    toks = _tokens(text)
    for i, tok in enumerate(toks):
        emo = _word_of(tok)
        if emo is None:
            continue
        value = _WEIGHT.get(tok, 1.0) * _modifier(toks, i)
        if _negated(toks, i):
            if emo == "joy":
                scores["sadness"] += value      # "not happy" leans sad, not happy
            else:
                scores[emo] += value * 0.2      # a negated bad word softens, not erases
        else:
            scores[emo] += value

    total   = sum(scores.values())
    primary = max(scores, key=scores.get)
    if scores[primary] <= 0:
        return {"primary": None, "secondary": None, "intensity": 0.0,
                "confidence": 0.0, "scores": scores}

    intensity  = min(1.0, scores[primary] / 3.0 * _emphasis(text))
    confidence = scores[primary] / total if total else 0.0
    # a real second feeling, only if it's close enough to the top to matter
    others    = {e: s for e, s in scores.items() if e != primary and s > 0}
    secondary = None
    if others:
        runner = max(others, key=others.get)
        if scores[runner] >= 0.5 * scores[primary]:
            secondary = runner

    return {"primary": primary, "secondary": secondary, "intensity": round(intensity, 3),
            "confidence": round(confidence, 3), "scores": scores}


# the emotion read is pluggable: the lexicon is the default floor; an optional
# local-transformer backend (core/emotion_nn) can plug in for a sharper read of
# context and tone, and refines its result against the lexicon's finer feelings.
# same {primary, secondary, intensity, confidence, scores} shape either way, so
# nothing downstream changes.
_BACKEND         = None
_BACKEND_CHECKED = False


def set_backend(fn):
    global _BACKEND
    _BACKEND = fn


def clear_backend():
    global _BACKEND, _BACKEND_CHECKED
    _BACKEND, _BACKEND_CHECKED = None, False


def _ensure_backend():
    # try once to wire the optional transformer backend, if it's installed
    global _BACKEND_CHECKED
    if _BACKEND_CHECKED or _BACKEND is not None:
        return
    _BACKEND_CHECKED = True
    try:
        from core import emotion_nn
        if emotion_nn.available():
            set_backend(emotion_nn.analyze)
    except Exception:
        pass


def analyze(text):
    # the deep read. uses the transformer backend when it's wired and working,
    # else the offline lexicon - and on any backend error, the lexicon catches it.
    _ensure_backend()
    if _BACKEND is not None:
        try:
            return _BACKEND(text)
        except Exception:
            pass
    return _lexicon_analyze(text)


def detect(text):
    # the old shape, kept stable for everything downstream: (emotion, intensity, scores).
    a = analyze(text)
    if a["primary"] is None:
        return "neutral", 0.0, a["scores"]
    return a["primary"], a["intensity"], a["scores"]
