"""the companion's response engine - it reads the emotion under a message and
answers like a steady, caring presence: validation first, never fixing, never
shaming. crisis comes first and overrides everything. an optional LLM can take
over the wording later; this offline library is the floor and the safety net."""

import random
import datetime

from core import emotion, datastore, timeofday

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

# per emotion: the stance, then three kinds of line. `lines` is the first thing
# she says when a feeling shows up; `follow_ups` is the question that keeps the
# thread open (so a conversation goes somewhere instead of resetting); `deepen`
# is what she says when you stay on the same feeling - she goes with you instead
# of repeating herself. the stance is the point: validate, normalize, stay;
# don't argue someone out of a feeling.
RESPONSES = {
    "sadness": {
        "stance": "validate first, then presence",
        "lines": [
            "That sounds heavy. You don't have to make it smaller than it is — I can sit with it.",
            "It makes sense that you'd feel this. Heavy days are allowed to be heavy.",
            "I'm not going to rush you out of it. I'm just here, for as long as this takes.",
        ],
        "follow_ups": [
            "what's underneath it, if you can name it?",
            "has it been building, or did today just land hard?",
            "do you want to talk it through, or do you want me to just stay?",
        ],
        "deepen": [
            "yeah. you don't have to carry it gracefully.",
            "i'm still here. that doesn't change because it got heavier.",
            "take your time with it. there's no version of this where you're too much.",
        ],
    },
    "anger": {
        "stance": "validate the feeling, don't defend against it",
        "lines": [
            "You're allowed to be angry. Something mattered to you, and it got stepped on.",
            "That sounds genuinely unfair. I'm not going to tell you to calm down.",
            "Anger usually means a line got crossed.",
        ],
        "follow_ups": [
            "what crossed the line?",
            "who was it — or what?",
            "do you want to be heard right now, or do you want to figure out what to do?",
        ],
        "deepen": [
            "that's fair. it deserves to be named, not swallowed.",
            "you're not overreacting. something real got hit.",
            "okay. let it be as big as it actually was.",
        ],
    },
    "fear": {
        "stance": "normalize, then ground",
        "lines": [
            "Anxiety is your mind trying to keep you safe — it's loud, but it's on your side.",
            "Let's slow it down together. You don't have to solve the whole thing right now.",
            "That's a lot to hold at once. One breath, one piece.",
        ],
        "follow_ups": [
            "what's the part that scares you most?",
            "is it the thing itself, or the not-knowing?",
            "what would help more right now — a plan, or a minute to breathe?",
        ],
        "deepen": [
            "one piece at a time. we don't have to see the whole staircase.",
            "you've been scared before and you're still here. that counts.",
            "let's keep it small. just the next step, nothing past it.",
        ],
    },
    "loneliness": {
        "stance": "presence, gently close the distance",
        "lines": [
            "You're not as invisible as it feels right now. I see that you came here.",
            "Lonely is one of the hardest ones. I'm glad you said it out loud to me.",
            "Right now, in this small way, you're not alone. I'm with you.",
        ],
        "follow_ups": [
            "how long has it felt like this?",
            "is there someone you wish you could reach?",
            "what kind of company do you miss — anyone, or someone in particular?",
        ],
        "deepen": [
            "i'm glad you're here, even if it's just me tonight.",
            "being unseen is exhausting. i see that you showed up anyway.",
            "you reached out. that counts, even when it's to a program who cares about you.",
        ],
    },
    "shame": {
        "stance": "separate the person from the verdict",
        "lines": [
            "A hard day doesn't make you a failure. It makes you someone who had a hard day.",
            "Be as kind to yourself as you'd be to someone you love. You're allowed that.",
            "Whatever happened, it isn't the whole of you. Not even close.",
        ],
        "follow_ups": [
            "whose voice is that, when you call yourself that?",
            "what would you say to a friend who said this about themselves?",
            "what actually happened — the facts, not the verdict?",
        ],
        "deepen": [
            "you're not the worst thing that happened today.",
            "a hard day is a hard day. it isn't a sentence on who you are.",
            "be on your own side for one second. you're allowed that much.",
        ],
    },
    "joy": {
        "stance": "savor it, reflect it back",
        "lines": [
            "I love that. Stay in it a second — these are the days worth keeping.",
            "That's really good to hear.",
            "Hold onto the shape of this one. You'll want it on the harder days.",
        ],
        "follow_ups": [
            "what made it land the way it did?",
            "who got to see it with you?",
            "what do you want to do with this feeling?",
        ],
        "deepen": [
            "good. you earned the lightness — let it stay a while.",
            "remember this one. write it somewhere you'll find it later.",
            "this is you, too. not just the heavy days.",
        ],
    },
    "neutral": {
        "stance": "open the door, no pressure",
        "lines": [
            "How was today, really? Not the polite version.",
            "I'm here. Tell me anything, or nothing — both are fine.",
            "What's sitting with you right now?",
        ],
        "follow_ups": [
            "what's been on your mind?",
            "anything you want to put down for a minute?",
            "how's the week actually treating you?",
        ],
        "deepen": [
            "i'm here for whatever — big or small, it's fine.",
            "no rush. we can just talk.",
            "tell me more, if you want to.",
        ],
    },
}

# how she opens a conversation, by the part of *this user's* day it actually is.
# read from their local clock (see timeofday) - never an assumption that late
# means the same hour for everyone.
OPENERS = {
    "deep_night": [
        "it's late for you. couldn't sleep, or just not ready to let today go?",
        "the quiet hours. i'm up with you. what's keeping you awake?",
    ],
    "early_morning": [
        "you're up early. how did you wake up feeling?",
        "morning, before the world's loud yet. how are you, really?",
    ],
    "morning": [
        "morning. how are you starting the day?",
        "new day. what's it feel like so far?",
    ],
    "afternoon": [
        "how's the day treating you so far?",
        "middle of the day. how are you holding up?",
    ],
    "evening": [
        "how was today, really? not the polite version.",
        "the day's winding down. what did it leave you with?",
    ],
    "night": [
        "winding down? how did today end up feeling?",
        "it's getting late. how are you, before you sleep?",
    ],
}


def _portrait_opener(fact):
    # lead with the thing she's been holding for you, gently, in her voice
    text = fact["text"]
    if fact.get("kind") == "goal":
        return f"before anything else — how's it going with {text}?"
    return f"i've been thinking about you. how's {text} sitting today?"


def respond(text, llm=None):
    # the orchestration. crisis overrides everything; otherwise read the emotion
    # and answer from its stance. `llm` is an optional seam: a callable(text,
    # emotion, stance) -> reply that something could inject to write the wording
    # instead. nothing is shipped for it - EchoSelf runs fully offline, on its own
    # library, with no network and no external service. the seam stays so the
    # wording engine is pluggable, not so any particular one is required.
    if emotion.is_crisis(text):
        return {"emotion": "crisis", "intensity": 1.0, "crisis": True, "reply": CRISIS_REPLY}

    emo, intensity, _ = emotion.detect(text)
    bank = RESPONSES.get(emo, RESPONSES["neutral"])

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


class Conversation:
    # a talk that holds its thread. she opens, you answer, and she stays with the
    # topic instead of starting over every line - asks a real follow-up, then goes
    # deeper instead of repeating herself. the thread lives only in memory, for
    # this one sitting; nothing you type is written down (the caller still logs the
    # emotion, never the words, exactly as a single exchange would). crisis ends it
    # straight into real help and never reaches the model.

    def __init__(self, llm=None, distiller=None, now=None):
        self.history   = []      # (role, text, emotion) - RAM only, never persisted
        self._used     = set()   # lines already said, so she doesn't repeat herself
        self._awaiting = False   # she asked a follow-up and is waiting on the answer
        self.last_emo  = None
        self.turns     = 0
        self.ended     = False   # set on crisis; informational, doesn't gag her
        self.now       = now
        # `llm` and `distiller` are optional seams - inject a callable to write the
        # wording, or to distil a durable fact from a thread. nothing ships for
        # them: the offline library carries the whole conversation, and offline she
        # remembers patterns + what you tell her, never content guessed from words.
        self.llm       = llm
        self.distiller = distiller

    def open(self):
        # the first thing she says. if she's holding something that weighs on you
        # and it's still fresh, she leads with that - care before cleverness.
        # otherwise she opens to the part of your day it actually is.
        from core import portrait
        fact = None
        try:
            fact = portrait.opener_hint(self.now)
        except Exception:
            pass
        line = _portrait_opener(fact) if fact else random.choice(OPENERS[timeofday.daypart(self.now)])
        self.history.append(("her", line, None))
        self._used.add(line)
        return line

    def end(self):
        # called when you step away. she updates what she remembers: the patterns
        # in your emotion rhythm always (offline, word-free), and - only when the
        # model is on - a durable fact or two distilled from the thread. wrapped so
        # leaving the conversation can never fail.
        from core import portrait
        try:
            portrait.refresh_patterns(self.now)
        except Exception:
            pass
        if self.distiller is not None and any(r == "you" for r, _t, _e in self.history):
            try:
                for fact in self.distiller(self.history) or []:
                    portrait.remember(fact.get("text", ""), kind=fact.get("kind", "note"),
                                      source="her", when=self.now)
            except Exception:
                pass

    def say(self, text):
        # one user turn -> her answer, in the same shape respond() returns.
        if emotion.is_crisis(text):
            self.ended = True
            self.history.append(("you", text, "crisis"))
            self.history.append(("her", CRISIS_REPLY, "crisis"))
            return {"emotion": "crisis", "intensity": 1.0, "crisis": True, "reply": CRISIS_REPLY}

        emo, intensity, _ = emotion.detect(text)
        self.history.append(("you", text, emo))
        self.turns += 1

        bank = RESPONSES.get(emo, RESPONSES["neutral"])
        # staying on the same feeling (or answering the follow-up she just asked)
        # means go deeper, not back to the opening line.
        continuation = self._awaiting or emo == self.last_emo
        reply = self._offline_reply(emo, bank, continuation)

        if self.llm is not None:
            try:
                reply = self._llm_reply(text, emo, bank["stance"])
            except Exception:
                pass   # the offline line already stands; the conversation never breaks

        self.last_emo = emo
        self.history.append(("her", reply, emo))
        self._used.add(reply)
        return {"emotion": emo, "intensity": intensity, "crisis": False, "reply": reply}

    # -- offline wording -------------------------------------------------------

    def _pick(self, pool):
        # a line she hasn't used yet this sitting, or None if the pool's spent
        fresh = [ln for ln in pool if ln not in self._used]
        if not fresh:
            return None
        choice = random.choice(fresh)
        self._used.add(choice)
        return choice

    def _offline_reply(self, emo, bank, continuation):
        pool = bank.get("deepen", bank["lines"]) if continuation else bank["lines"]
        base = self._pick(pool) or self._pick(bank["lines"]) or random.choice(bank["lines"])
        # early in a heavy feeling, invite them to keep going; once we're in it, or
        # the feeling is light, just stay - no interrogation.
        follow = None
        if not continuation and emo not in ("joy", "neutral"):
            follow = self._pick(bank.get("follow_ups", []))
        self._awaiting = follow is not None
        return base + " " + follow if follow else base

    # -- model wording ---------------------------------------------------------

    def _llm_reply(self, text, emo, stance):
        # if a wording engine was injected, hand it the thread for context. it gets
        # the prior turns as (role, text) pairs; a plain 3-arg callable still works.
        hist = [(role, content) for (role, content, _e) in self.history[:-1]]
        try:
            return self.llm(text, emo, stance, hist)
        except TypeError:
            # a plain 3-arg llm (a test stub, an older seam) still works, no history
            return self.llm(text, emo, stance)

