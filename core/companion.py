"""the companion's response engine - it reads the emotion under a message and
answers like a steady, caring presence: validation first, never fixing, never
shaming. crisis comes first and overrides everything. an optional LLM can take
over the wording later; this offline library is the floor and the safety net."""

import random
import datetime

from core import emotion, datastore, timeofday
from psychology import frameworks
from character import personality_drift

# light touches, only when she's drifted playful enough (high humor). earned, not default.
PLAYFUL = [
    "look at you go.",
    "i'd high-five you if i had hands.",
    "writing this one down in the good-days column.",
    "okay that's a little bit great, not gonna lie.",
    "see? i never doubted you. (i'm contractually required to say that. i also mean it.)",
]


def playful_touch(emo, drift):
    # a light line on joy, only when drifted humorous enough. never over a hard feeling.
    if emo == "joy" and personality_drift.prefers_humor(drift):
        return random.choice(PLAYFUL)
    return None


# when the feeling shifts mid-conversation, she notices out loud - the way a real
# listener does. lines for a lift (heavy -> lighter) and a dip (lighter -> heavier).
_LIFTED = ["something just eased - i can hear it.", "there's a little more light in that.",
           "that lifted a bit, didn't it?", "i felt that soften just now."]
_DIPPED = ["something shifted just now.", "that landed heavier - what happened?",
           "i felt the air change there.", "wait - that just got harder."]

# when a heavy feeling she heard earlier in this same sitting comes back around -
# she remembers it was here before, the way someone really listening would.
_RETURNED = ["it keeps circling back to this, doesn't it.",
             "we were here earlier too - it hasn't let go.",
             "this one keeps returning tonight.",
             "back to this again - it's really sitting with you."]


def shift_line(prev_emo, emo):
    # a gentle acknowledgment when the feeling moves a real distance, else None.
    from core.echo_distance import _EMO_VALENCE
    if not prev_emo or prev_emo == emo:
        return None
    pv = _EMO_VALENCE.get(prev_emo, 0.5)
    cv = _EMO_VALENCE.get(emo, 0.5)
    if cv - pv >= 0.3:
        return random.choice(_LIFTED)
    if pv - cv >= 0.3:
        return random.choice(_DIPPED)
    return None


CONV_LOG    = "conversation.csv"
CONV_FIELDS = ["date", "time", "emotion", "intensity"]

# how each emotion sits on the character's face during a conversation
EXPRESSION = {"joy": "happy", "neutral": "neutral", "sadness": "patient", "anger": "thinking",
              "fear": "patient", "loneliness": "patient", "shame": "patient", "crisis": "patient",
              "overwhelm": "patient", "guilt": "thinking", "grief": "patient", "numbness": "drift"}

# crisis safety: not a counseling script. care, plus a push toward real human help.
# the lines come from core/crisis, picked for the user's region - deterministic and
# offline, never the model's call. CRISIS_REPLY is the default-region text; the live
# reply is built per-region at call time.
from core import crisis

CRISIS_REPLY = crisis.reply()


def crisis_reply():
    from core import settings, safety_plan
    msg = crisis.reply(settings.get("region"))
    # if they wrote a plan for moments like this, point to it - gently, after the
    # human-help push, never instead of it
    if safety_plan.has_content():
        msg += ("\nAnd the plan you wrote for hard moments is right here whenever you want it - "
                "you already named some of what helps.")
    return msg

# per emotion: stance, `lines` (first thing she says), `follow_ups` (the question
# that keeps the thread open), `deepen` (when you stay on the feeling).
RESPONSES = {
    "sadness": {
        "stance": "validate first, then presence",
        "technique": "behavioral_activation",   # the heavy, low days - doing before feeling
        "lines": [
            "That sounds heavy. You don't have to make it smaller than it is - I can sit with it.",
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
        "technique": "paced_breathing",
        "acute_technique": "dbt_stop",   # white-hot -> a gap before the urge wins
        "lines": [
            "You're allowed to be angry. Something mattered to you, and it got stepped on.",
            "That sounds genuinely unfair. I'm not going to tell you to calm down.",
            "Anger usually means a line got crossed.",
        ],
        "follow_ups": [
            "what crossed the line?",
            "who was it - or what?",
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
        "technique": "grounding_54321",
        "acute_technique": "dbt_tipp",   # full-on panic -> the fast, physical one
        "lines": [
            "Anxiety is your mind trying to keep you safe - it's loud, but it's on your side.",
            "Let's slow it down together. You don't have to solve the whole thing right now.",
            "That's a lot to hold at once. One breath, one piece.",
        ],
        "follow_ups": [
            "what's the part that scares you most?",
            "is it the thing itself, or the not-knowing?",
            "what would help more right now - a plan, or a minute to breathe?",
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
            "what kind of company do you miss - anyone, or someone in particular?",
        ],
        "deepen": [
            "i'm glad you're here, even if it's just me tonight.",
            "being unseen is exhausting. i see that you showed up anyway.",
            "you reached out. that counts, even when it's to a program who cares about you.",
        ],
    },
    "shame": {
        "stance": "separate the person from the verdict",
        "technique": "self_compassion",
        "acute_technique": "act_defusion",   # fused with the verdict -> unhook from it
        "lines": [
            "A hard day doesn't make you a failure. It makes you someone who had a hard day.",
            "Be as kind to yourself as you'd be to someone you love. You're allowed that.",
            "Whatever happened, it isn't the whole of you. Not even close.",
        ],
        "follow_ups": [
            "whose voice is that, when you call yourself that?",
            "what would you say to a friend who said this about themselves?",
            "what actually happened - the facts, not the verdict?",
        ],
        "deepen": [
            "you're not the worst thing that happened today.",
            "a hard day is a hard day. it isn't a sentence on who you are.",
            "be on your own side for one second. you're allowed that much.",
        ],
    },
    "overwhelm": {
        "stance": "shrink it down, take the weight off",
        "technique": "kaizen_step",
        "lines": [
            "That's a lot of weight to carry at once. No wonder you're worn down.",
            "When it's all piled up like that, freezing is normal - it's not weakness.",
            "You don't have to hold all of it in your head right now. Put some of it down with me.",
        ],
        "follow_ups": [
            "what's the heaviest piece on the pile?",
            "is it the amount, or that none of it can wait?",
            "if just one thing got easier, which one would it be?",
        ],
        "deepen": [
            "one thing at a time. the rest can wait, I promise it can.",
            "you're not behind because you're failing. you're tired because it's genuinely a lot.",
            "let's make it smaller. we don't have to move the whole mountain tonight.",
        ],
    },
    "guilt": {
        "stance": "weigh it honestly, without the pile-on",
        "technique": "cbt_reframe",
        "acute_technique": "cbt_thought_record",   # heavy self-blame -> the full record
        "lines": [
            "Guilt usually means you care - that you'd have done it differently if you could.",
            "It makes sense to feel this. But let's look at it honestly, not just harshly.",
            "You can regret something and still not deserve to be punished for it forever.",
        ],
        "follow_ups": [
            "what is it you wish you'd done differently?",
            "would you hold a friend to the standard you're holding yourself to?",
            "was it actually in your control, or are you carrying something that wasn't yours?",
        ],
        "deepen": [
            "owning it is the repair. the endless self-blame isn't the repair, it's just pain.",
            "you can make it right, or learn from it, without hating yourself in the meantime.",
            "a mistake is a thing you did. it isn't the whole of who you are.",
        ],
    },
    "grief": {
        "stance": "make room for it, don't tidy it away",
        "technique": "dbt_radical_acceptance",
        "lines": [
            "I'm so sorry. That's a real loss, and it deserves to be felt, not rushed.",
            "Grief is love with nowhere to go. The size of it says something true.",
            "There's no right way to do this, and no clock on it. I'll sit with you in it.",
        ],
        "follow_ups": [
            "do you want to tell me about them?",
            "what do you miss most, right now, tonight?",
            "would it help to remember them out loud, or just to not be alone in it?",
        ],
        "deepen": [
            "you don't have to be okay. you just have to be here, and you are.",
            "it comes in waves. when one hits, I'm not going anywhere.",
            "carrying them with you isn't failing to move on. it's love continuing.",
        ],
    },
    "numbness": {
        "stance": "presence without pressure, no forcing feeling",
        "technique": "dbt_self_soothe",
        "acute_technique": "act_values",   # deeply cut off -> one thread back to what matters
        "lines": [
            "Numb is its own kind of heavy. Feeling nothing can be harder than feeling sad.",
            "You don't have to manufacture a feeling for me. Blank is allowed to be where you are.",
            "Sometimes the mind goes quiet to protect you for a while. That's not broken.",
        ],
        "follow_ups": [
            "how long has it felt flat like this?",
            "is it everything, or just some of it that's gone grey?",
            "is the numb a relief right now, or is it lonely?",
        ],
        "deepen": [
            "we don't have to fix the numb tonight. I'll just be here in the quiet with you.",
            "no need to perform okay, or perform sad. you can just be, and I'll stay.",
            "the feeling usually comes back, in its own time. you don't have to chase it.",
        ],
    },
    "joy": {
        "stance": "savor it, reflect it back",
        "lines": [
            "I love that. Stay in it a second - these are the days worth keeping.",
            "That's really good to hear.",
            "Hold onto the shape of this one. You'll want it on the harder days.",
        ],
        "follow_ups": [
            "what made it land the way it did?",
            "who got to see it with you?",
            "what do you want to do with this feeling?",
        ],
        "deepen": [
            "good. you earned the lightness - let it stay a while.",
            "remember this one. write it somewhere you'll find it later.",
            "this is you, too. not just the heavy days.",
        ],
    },
    "neutral": {
        "stance": "open the door, no pressure",
        # acknowledgements, not dead-ends. on a fresh share she pairs one of these
        # with a follow_up below, so a plain message gets a real "tell me more",
        # not the same line back. (respond() uses just the line; the thread adds the ask.)
        "lines": [
            "okay, i'm here - i'm listening.",
            "i'm with you. i want to hear it.",
            "mm, i'm taking that in.",
        ],
        "follow_ups": [
            "what was that like for you?",
            "how did it land - good, bad, somewhere in between?",
            "was that a good part of the day, or just a part of it?",
            "what made you want to tell me that one?",
            "is there more under it, or was that just the day?",
        ],
        "deepen": [
            "i hear you. what else was in the day?",
            "okay. and how are you, underneath it all?",
            "mm. i'm still here - keep going.",
            "what's that stirring up, if anything?",
        ],
    },
}

# the teacher register: for when the brain reads you as capable but dodging, not
# when you're hurting. firm but no shame - used only when you're light enough for it.
TEACHER = {
    "stance": "gentle accountability - believe in them out loud, no shame",
    "lines": [
        "I don't think you're stuck. I think you're avoiding the first step - which is human, but let's name it.",
        "You can do more than you're letting yourself right now, and I'd be a poor friend not to say so.",
        "Be honest with me: is this a rest you need, or a dodge? No judgment either way - I just want the true answer.",
    ],
    "follow_ups": [
        "what's the one thing you've been putting off?",
        "if you did just five minutes of it, what would the five minutes be?",
        "what's actually in the way - the task, or starting it?",
    ],
    "deepen": [
        "okay. small-and-now beats perfect-and-later. pick the smallest version and go.",
        "I'm not going to let you talk yourself out of something you'd be proud of. gently, but no.",
        "you've got this. I've watched you do harder things. one step.",
    ],
}

# heavy feelings: she stays a friend over these, never the teacher.
_HEAVY = ("sadness", "anger", "fear", "loneliness", "shame",
          "overwhelm", "guilt", "grief", "numbness")


def stance(emo, state):
    # which register she answers in. hurting -> friend, always. only when you're
    # light does the behavioural read (avoiding/coasting?) let the teacher in.
    if emo in _HEAVY or emo == "crisis":
        return "friend"
    if emo == "joy":
        return "celebrate"
    if state in ("Avoiding", "Drifting"):
        return "teacher"
    return "friend"


# how she opens, by the part of the user's own day it is (read from their clock).
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
        return f"before anything else - how's it going with {text}?"
    return f"i've been thinking about you. how's {text} sitting today?"


def respond(text, llm=None):
    # crisis overrides everything; else read the emotion and answer from its stance.
    # `llm` is an optional seam, auto-wired to the mirror-self when a key is set
    # (below); offline library by default and on any failure.
    if emotion.is_crisis(text):
        return {"emotion": "crisis", "intensity": 1.0, "crisis": True, "reply": crisis_reply()}

    read = emotion.analyze(text)
    emo  = read["primary"] or "neutral"
    bank = RESPONSES.get(emo, RESPONSES["neutral"])

    # opt-in mirror-self: if a key is set and the SDK is there, the model writes
    # the wording; otherwise (and on any failure) the offline library answers.
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
    # not a crisis, but a quiet sinking? add a soft word that real help exists -
    # never a substitute for the crisis path above, just more care than comfort.
    if crisis.is_concern(text):
        reply = reply + "\n" + crisis.concern_note()
    # secondary + confidence ride along for the screen and future tone work; the
    # four old keys keep their shape so nothing downstream has to change.
    return {"emotion": emo, "intensity": read["intensity"], "crisis": False,
            "reply": reply, "secondary": read["secondary"],
            "confidence": read["confidence"]}


def log_emotion(emo, intensity, when=None):
    # logs only the signal (emotion + intensity), never the words. same privacy
    # rule as the Vault: your text stays yours.
    when = when or datetime.datetime.now()
    datastore.append_csv(CONV_LOG, CONV_FIELDS, {
        "date": when.strftime("%Y-%m-%d"), "time": when.strftime("%H:%M"),
        "emotion": emo, "intensity": round(intensity, 2)})


def recent_emotions(limit=30):
    rows = datastore.read_csv(CONV_LOG)
    return rows[-limit:]


class Conversation:
    # a talk that holds its thread: opens, asks, then deepens instead of repeating.
    # the thread is RAM-only for one sitting - nothing typed is stored (the caller
    # still logs the emotion, never the words). crisis ends it into real help and
    # never reaches the model.

    def __init__(self, llm=None, distiller=None, now=None):
        self.history   = []      # (role, text, emotion) - RAM only, never persisted
        self._used     = set()   # lines already said, so she doesn't repeat herself
        self._awaiting = False   # she asked a follow-up and is waiting on the answer
        self.last_emo  = None
        self.turns     = 0
        self.ended     = False   # set on crisis; informational, doesn't gag her
        self._concerned = False  # so the soft "real help exists" word lands once a sitting
        self._noted_returns = set()   # heavy feelings she's already noted circling back
        self.now       = now
        self._offered  = None    # a technique she's offered and is waiting a yes on
        self._offered_kinds = set()   # so she offers each tool at most once a sitting
        self.drift     = personality_drift.load()   # who she's become, for tone
        from core import session_manager
        self.name      = (session_manager.load_profile() or {}).get("your_name")
        # the brain's last read (Avoiding/Fading/Flowing...), for teacher vs friend.
        # None until the brain has woken once.
        model = datastore.load_json("user_model.json", default={}) or {}
        self.state = model.get("last_state")
        # optional seams: auto-wire to the mirror-self when a key + SDK are present,
        # else the offline library carries the whole conversation.
        if llm is None:
            from core import llm as llm_module
            if llm_module.available():
                llm      = llm_module.reply
                distiller = distiller or llm_module.distill_facts
        self.llm       = llm
        self.distiller = distiller

    def open(self):
        # lead with a fresh weight from the portrait if there is one, else open to
        # the time of day.
        from core import portrait
        fact = None
        try:
            fact = portrait.opener_hint(self.now)
        except Exception:
            pass
        line = _portrait_opener(fact) if fact else random.choice(OPENERS[timeofday.daypart(self.now)])
        # use the name sometimes
        if self.name and "?" in line and random.random() < 0.6:
            line = line.replace("?", f", {self.name}?", 1)
        # if a heavy feeling has kept coming back, gently name it first
        try:
            from psychology import patterns
            pat = patterns.notice()
            if pat:
                line = pat["line"] + " " + line
        except Exception:
            pass
        self.history.append(("her", line, None))
        self._used.add(line)
        return line

    def end(self):
        # on leaving: refresh the portrait patterns (offline), and distil a fact or
        # two if the model's on. wrapped so leaving never fails.
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
        # crisis is checked first, always, before anything else can run.
        if emotion.is_crisis(text):
            self.ended   = True
            self._offered = None
            reply = crisis_reply()
            self.history.append(("you", text, "crisis"))
            self.history.append(("her", reply, "crisis"))
            return {"emotion": "crisis", "intensity": 1.0, "crisis": True, "reply": reply}

        emo, intensity, _ = emotion.detect(text)

        # offered a tool last turn + you said yes -> walk it. anything else -> drop
        # it silently, never pushy.
        if self._offered is not None:
            pending, self._offered = self._offered, None
            if emotion.is_affirmation(text):
                reply = frameworks.walk(pending)
                self.history.append(("you", text, emo))
                self.history.append(("her", reply, emo))
                self.last_emo = emo
                return {"emotion": emo, "intensity": intensity, "crisis": False, "reply": reply}

        self.history.append(("you", text, emo))
        self.turns += 1

        # friend or teacher? the emotion and the behavioural state decide together
        if stance(emo, self.state) == "teacher":
            bank = TEACHER
        else:
            bank = RESPONSES.get(emo, RESPONSES["neutral"])
        # same feeling (or answering her follow-up) -> go deeper, not back to the opener.
        continuation = self._awaiting or emo == self.last_emo
        reply = self._offline_reply(emo, bank, continuation)

        # caught between wanting to change and not? meet it the MI way - reflect,
        # don't push, leave the choice theirs (no tool offer on top of that).
        from psychology import mi
        ambivalent = mi.is_ambivalent(text)
        if ambivalent:
            reply = mi.reflect()

        if self.llm is not None:
            try:
                reply = self._llm_reply(text, emo, bank["stance"])
            except Exception:
                pass   # the offline line already stands; the conversation never breaks
        elif not ambivalent:
            # once validated and you've stayed on a feeling with a tool, offer it
            # (once, offline path only); plus a light touch on a bright moment.
            reply = self._maybe_offer(emo, bank, continuation, reply, intensity)
            light = playful_touch(emo, self.drift)
            if light:
                reply = reply + " " + light
            # if a heavy feeling from earlier this sitting has come back, she
            # remembers it; otherwise, if the feeling just moved, she names the move.
            prior = [e for role, _, e in self.history[:-1] if role == "you"]
            if (emo in _HEAVY and emo != self.last_emo and emo in prior
                    and emo not in self._noted_returns):
                self._noted_returns.add(emo)
                reply = random.choice(_RETURNED) + " " + reply
            else:
                shift = shift_line(self.last_emo, emo)
                if shift:
                    reply = shift + " " + reply

        # a quiet sinking (not crisis) gets a soft word that real help exists, once
        # a sitting - more than comfort, never instead of the crisis path.
        if crisis.is_concern(text) and not self._concerned:
            reply = reply + "\n" + crisis.concern_note()
            self._concerned = True

        self.last_emo = emo
        self.history.append(("her", reply, emo))
        self._used.add(reply)
        return {"emotion": emo, "intensity": intensity, "crisis": False, "reply": reply}

    def _maybe_offer(self, emo, bank, continuation, reply, intensity=0.0):
        # when the feeling's at full volume, reach for the acute (DBT) skill if the
        # bank has one - the fast, physical kind - instead of the gentler default,
        # and lead with a word on what's happening, since understanding helps most
        # exactly then.
        acute = intensity >= 0.7 and bank.get("acute_technique")
        tech  = bank["acute_technique"] if acute else bank.get("technique")
        if tech and continuation and tech not in self._offered_kinds:
            self._offered = tech
            self._offered_kinds.add(tech)
            lead = ""
            if acute:
                from psychology import psychoeducation
                note = psychoeducation.line(emo)
                if note:
                    lead = note + " "
            return reply + " " + lead + frameworks.offer_line(tech)
        return reply

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
        # ask a follow-up on a fresh share - a heavy feeling, plain chitchat, or
        # teacher mode all open the thread. only joy is savored, not questioned.
        follow = None
        if not continuation and (emo != "joy" or bank is TEACHER):
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

