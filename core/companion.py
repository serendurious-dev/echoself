"""the companion's response engine - it reads the emotion under a message and
answers like a steady, caring presence: validation first, never fixing, never
shaming. crisis comes first and overrides everything. an optional LLM can take
over the wording later; this offline library is the floor and the safety net."""

import random
import datetime

from core import emotion, datastore

CONV_LOG    = "conversation.csv"
CONV_FIELDS = ["date", "time", "emotion", "intensity"]

# how each emotion sits on the character's face during a conversation
EXPRESSION = {"joy": "happy", "neutral": "neutral", "sadness": "patient", "anger": "thinking",
              "fear": "patient", "loneliness": "patient", "shame": "patient", "crisis": "patient"}

# crisis safety. this is not a counseling script and EchoSelf is not a clinician -
# the only job here is care plus a push toward a real human who can help, now.
CRISIS_REPLY = (
    "I'm really glad you told me, and I'm staying right here with you.\n"
    "What you're carrying sounds like more than anyone should carry alone — and I'm a program, "
    "not a person who can keep you safe tonight. Please reach out to someone who can, right now: "
    "a crisis line, a doctor, or someone you trust.\n"
    "If you're in immediate danger, contact your local emergency number. In South Korea you can "
    "call 109 (suicide prevention), or 1393. You deserve a real voice on the other end. "
    "I'll be here when you come back."
)

# per emotion: the stance, then a few lines written from it. the stance is the
# point - validate, normalize, stay; don't argue someone out of a feeling.
RESPONSES = {
    "sadness": {
        "stance": "validate first, then presence",
        "lines": [
            "That sounds heavy. You don't have to make it smaller than it is — I can sit with it.",
            "It makes sense that you'd feel this. Heavy days are allowed to be heavy.",
            "I'm not going to rush you out of it. I'm just here, for as long as this takes.",
        ],
    },
    "anger": {
        "stance": "validate the feeling, don't defend against it",
        "lines": [
            "You're allowed to be angry. Something mattered to you, and it got stepped on.",
            "That sounds genuinely unfair. I'm not going to tell you to calm down.",
            "Anger usually means a line got crossed. What was the line?",
        ],
    },
    "fear": {
        "stance": "normalize, then ground",
        "lines": [
            "Anxiety is your mind trying to keep you safe — it's loud, but it's on your side.",
            "Let's slow it down together. You don't have to solve the whole thing right now.",
            "That's a lot to hold at once. One breath, one piece. I'm here.",
        ],
    },
    "loneliness": {
        "stance": "presence, gently close the distance",
        "lines": [
            "You're not as invisible as it feels right now. I see that you came here.",
            "Lonely is one of the hardest ones. I'm glad you said it out loud to me.",
            "Right now, in this small way, you're not alone. I'm with you.",
        ],
    },
    "shame": {
        "stance": "separate the person from the verdict",
        "lines": [
            "A hard day doesn't make you a failure. It makes you someone who had a hard day.",
            "Be as kind to yourself as you'd be to someone you love. You're allowed that.",
            "Whatever happened, it isn't the whole of you. Not even close.",
        ],
    },
    "joy": {
        "stance": "savor it, reflect it back",
        "lines": [
            "I love that. Stay in it a second — these are the days worth keeping.",
            "That's really good to hear. What made it land the way it did?",
            "Hold onto the shape of this one. You'll want it on the harder days.",
        ],
    },
    "neutral": {
        "stance": "open the door, no pressure",
        "lines": [
            "How was today, really? Not the polite version.",
            "I'm here. Tell me anything, or nothing — both are fine.",
            "What's sitting with you right now?",
        ],
    },
}


def respond(text, llm=None):
    # the orchestration. crisis overrides everything; otherwise read the emotion
    # and answer from its stance. `llm`, when given, is a callable(text, emotion,
    # stance) -> reply for the optional richer path - the offline library is the
    # fallback and is always what runs without a key.
    if emotion.is_crisis(text):
        return {"emotion": "crisis", "intensity": 1.0, "crisis": True, "reply": CRISIS_REPLY}

    emo, intensity, _ = emotion.detect(text)
    bank = RESPONSES.get(emo, RESPONSES["neutral"])

    # the hybrid brain: if a key is set and the SDK is there, Claude takes over
    # the wording. otherwise (and on any failure) the offline library answers.
    if llm is None:
        from core import llm as llm_module
        if llm_module.available():
            llm = llm_module.reply

    if llm is not None:
        try:
            reply = llm(text, emo, bank["stance"])
        except Exception:
            reply = random.choice(bank["lines"])
    else:
        reply = random.choice(bank["lines"])
    return {"emotion": emo, "intensity": intensity, "crisis": False, "reply": reply}


def log_emotion(emo, intensity, when=None):
    # the conversation log keeps only the *signal* - the inferred emotion and how
    # strong it was - never the words. that is what the inner world will learn
    # from, and it honors the same privacy as the Vault: your text stays yours.
    when = when or datetime.datetime.now()
    datastore.append_csv(CONV_LOG, CONV_FIELDS, {
        "date": when.strftime("%Y-%m-%d"), "time": when.strftime("%H:%M"),
        "emotion": emo, "intensity": round(intensity, 2)})


def recent_emotions(limit=30):
    rows = datastore.read_csv(CONV_LOG)
    return rows[-limit:]

