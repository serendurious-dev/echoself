"""read emotion from how someone writes - sad, angry, anxious, lonely, ashamed,
joyful - without ever asking. lexicon-based and offline; the LLM layer can
refine this later, but the floor works with no network."""

import re

EMOTIONS = ["joy", "sadness", "anger", "fear", "loneliness", "shame"]

# small but real word lists. not exhaustive - the point is to read the drift of
# a message, not to diagnose it.
_LEX = {
    "joy":        ["happy", "glad", "great", "good", "excited", "wonderful", "amazing",
                   "grateful", "relieved", "proud", "content", "calm", "peaceful", "hopeful",
                   "fun", "joy", "joyful", "smiling", "better", "lighter", "okay", "fine"],
    "sadness":    ["sad", "down", "low", "unhappy", "depressed", "empty", "hopeless", "crying",
                   "cry", "exhausted", "drained", "hurt", "miserable", "heavy", "numb", "lost",
                   "disappointed", "grief", "tired", "defeated"],
    "anger":      ["angry", "mad", "furious", "annoyed", "irritated", "frustrated", "rage",
                   "hate", "resent", "unfair", "fed", "sick"],
    "fear":       ["anxious", "afraid", "scared", "worried", "nervous", "panic", "panicking",
                   "stressed", "overwhelmed", "terrified", "uneasy", "dread", "fear", "tense"],
    "loneliness": ["alone", "lonely", "isolated", "ignored", "unseen", "nobody", "abandoned",
                   "invisible", "disconnected"],
    "shame":      ["ashamed", "embarrassed", "guilty", "worthless", "stupid", "failure",
                   "useless", "inadequate", "pathetic"],
}

# a few multi-word cues that a single-word scan would miss
_PHRASES = {
    "shame":      ["not good enough", "not enough", "let everyone down", "messed up"],
    "loneliness": ["no one", "left out", "by myself", "on my own"],
    "sadness":    ["give up", "giving up", "can't anymore", "what's the point"],
}

_NEGATIONS = {"not", "no", "never", "isnt", "isn't", "wasnt", "wasn't", "dont", "don't",
              "didnt", "didn't", "cant", "can't", "wont", "won't", "arent", "aren't",
              "hardly", "barely", "aint", "ain't"}

# crisis comes first, always. these never get "handled" by the normal path -
# they trigger care and a push toward real, human help (see companion.py).
# err toward catching - missing a real one is far worse than catching a false one
_CRISIS = ["kill myself", "killing myself", "end my life", "ending my life",
           "end it all", "ending it all", "end it", "suicide", "suicidal",
           "want to die", "wanna die", "don't want to live", "do not want to live",
           "dont want to be here", "hurt myself", "harm myself", "self harm",
           "self-harm", "no reason to live", "better off dead", "can't go on",
           "cant go on", "can't do this anymore", "cant do this anymore"]


def is_crisis(text):
    t = text.lower()
    return any(phrase in t for phrase in _CRISIS)


def _tokens(text):
    return re.findall(r"[a-z']+", text.lower())


def detect(text):
    # returns (emotion, intensity 0..1, scores). neutral when nothing registers.
    low = text.lower()
    scores = {e: 0.0 for e in EMOTIONS}

    for emo, phrases in _PHRASES.items():
        for p in phrases:
            if p in low:
                scores[emo] += 1.5

    toks = _tokens(text)
    for i, tok in enumerate(toks):
        negated = i > 0 and toks[i - 1] in _NEGATIONS
        for emo, words in _LEX.items():
            if tok in words:
                if emo == "joy" and negated:
                    scores["sadness"] += 1.0     # "not happy" leans sad, not happy
                elif negated:
                    scores[emo] += 0.2           # a negated bad word softens, not erases
                else:
                    scores[emo] += 1.0

    emo = max(scores, key=scores.get)
    if scores[emo] <= 0:
        return "neutral", 0.0, scores
    return emo, min(1.0, scores[emo] / 3.0), scores
