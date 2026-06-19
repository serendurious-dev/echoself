"""optional local-transformer backend for the emotion read.

free and offline - a small emotion model runs on your machine, nothing leaves it.
EchoSelf works fine without this (the lexicon in core/emotion is the floor); this
just reads context and tone more sharply. install via requirements-nlp.txt; the
model downloads once on first use. set ECHOSELF_NLP_MODEL to swap it.

the model only knows a handful of broad feelings, so we keep the lexicon's finer
ones (shame, guilt, grief, loneliness, overwhelm, numbness): when the lexicon
names one of those clearly, it wins; otherwise the model's read does."""

import importlib.util
import os

DEFAULT_MODEL = "j-hartmann/emotion-english-distilroberta-base"
MODEL_ENV     = "ECHOSELF_NLP_MODEL"

# the model's labels -> our emotions. it can't name the fine ones; that's the
# lexicon's job in _blend.
_LABEL_MAP = {"anger": "anger", "disgust": "anger", "fear": "fear", "joy": "joy",
              "sadness": "sadness", "neutral": "neutral", "surprise": "joy"}

# feelings only the lexicon can name - if it sees one clearly, trust it over the
# model's coarser bucket
_FINE = {"loneliness", "shame", "overwhelm", "guilt", "grief", "numbness"}

_pipe = None


def available():
    # just the deps - cheap, never loads the model
    return all(importlib.util.find_spec(m) is not None for m in ("transformers", "torch"))


def _label_to_emotion(label):
    return _LABEL_MAP.get(str(label).lower(), "neutral")


def _blend(coarse, score, lex):
    # coarse = the model's mapped emotion + its probability; lex = the lexicon read.
    # keep a fine feeling the lexicon named clearly; else go with the model.
    primary    = coarse
    if lex.get("primary") in _FINE and lex.get("confidence", 0) >= 0.5:
        primary = lex["primary"]
    intensity  = round(max(float(score), lex.get("intensity", 0.0)), 3)
    confidence = round(float(score), 3)
    return {"primary": primary, "secondary": lex.get("secondary"),
            "intensity": intensity, "confidence": confidence,
            "scores": {"model": {coarse: round(float(score), 3)}, "lexicon": lex.get("scores", {})}}


def _pipeline():
    global _pipe
    if _pipe is None:
        from transformers import pipeline
        _pipe = pipeline("text-classification",
                         model=os.environ.get(MODEL_ENV, DEFAULT_MODEL), top_k=1)
    return _pipe


def analyze(text):
    # the model's read, blended with the lexicon's finer feelings. raises on any
    # failure so core/emotion falls back to the lexicon.
    from core.emotion import _lexicon_analyze
    out   = _pipeline()(text)
    top   = out[0][0] if isinstance(out[0], list) else out[0]   # pipeline shape varies
    coarse = _label_to_emotion(top["label"])
    return _blend(coarse, top["score"], _lexicon_analyze(text))
