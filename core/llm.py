"""the optional mirror-self: when you've added your own key, Claude writes the
companion's reply *as your better self* - the version of you that made it,
speaking back to you, conditioned on what she's learned about you (your portrait
and your ideal self from Session Zero).

this is opt-in and off by default. EchoSelf runs fully offline without it; this
only activates when ANTHROPIC_API_KEY is set and the anthropic SDK is installed.
it never sees a crisis message (companion.py handles those before it gets here),
and on any failure the caller falls back to the offline library, so the
conversation never breaks. nothing here is required - it's a layer you switch on."""

import os

MODEL_ENV     = "ECHOSELF_LLM_MODEL"
DEFAULT_MODEL = "claude-sonnet-4-6"


def available():
    # only when the user has opted in (their own key) and the SDK is installed
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False


def _mirror_system(emotion, stance):
    # build the "your better self" persona from what's actually known about the
    # user - their ideal self and the portrait. all local; we send only what's
    # needed to sound like them, never the raw conversation log.
    from core import session_manager, portrait
    profile = session_manager.load_profile() or {}
    name    = profile.get("your_name")
    ideal   = profile.get("ideal_self", {}) or {}
    facts   = []
    try:
        facts = [f["text"] for f in portrait.facts()][:8]
    except Exception:
        facts = []

    who = ideal.get("name") or "the version of them that made it"
    lines = [
        f"You are {who} - the person you're speaking with, at their wisest and kindest, "
        "talking back to themselves. You are not a generic assistant. You are them, turned "
        "toward themselves with love.",
        "The rule is presence over pressure: validate first, never shame, never lecture, never "
        "give medical or clinical advice. You are a companion, not a clinician.",
    ]
    if name:
        lines.append(f"Their name is {name}; use it naturally, not in every line.")
    if ideal.get("core_trait"):
        lines.append(f"What they're reaching to become: {ideal['core_trait']}.")
    if ideal.get("values"):
        lines.append("What they won't give up: " + ", ".join(v for v in ideal["values"] if v) + ".")
    if facts:
        lines.append("What's been on them lately (hold it lightly, never recite it back): "
                     + "; ".join(facts) + ".")
    lines.append(f"Right now the feeling under their words reads as '{emotion}', and your stance "
                 f"is '{stance}'. Answer in one to four short, human sentences - warm, real, a "
                 "little of their own voice, the way they'd talk to themselves on a good day. No "
                 "bullet points, no 'as an AI'. If they ever sound in real danger, gently urge "
                 "them toward a real person or a crisis line.")
    return "\n".join(lines)


def reply(text, emotion, stance, history=None):
    # one short reply, in the user's better-self voice, with the thread for context.
    # raises on any failure so the caller falls back to the offline library.
    import anthropic
    client = anthropic.Anthropic()

    messages = [{"role": "assistant" if role == "her" else "user", "content": content}
                for role, content in (history or [])]
    while messages and messages[0]["role"] == "assistant":
        messages.pop(0)
    messages.append({"role": "user", "content": text})

    message = client.messages.create(
        model=os.environ.get(MODEL_ENV, DEFAULT_MODEL),
        max_tokens=300,
        system=_mirror_system(emotion, stance),
        messages=messages,
    )
    out = next((b.text for b in message.content if b.type == "text"), "").strip()
    if not out:
        raise RuntimeError("empty reply from the model")
    return out


_RESEARCH_SYSTEM = (
    "You are looking something up for the person you're talking with. Your one hard "
    "rule, above everything: never make anything up. Use web search to find the "
    "answer. If the search gives you a clear, well-sourced answer, say it plainly in "
    "two or three sentences and name where it came from. If you cannot verify it - if "
    "the sources disagree, or you just can't find it - say exactly that, 'I couldn't "
    "find a reliable answer to that,' and stop. Do not guess, ever, not even a little. "
    "A wrong answer is worse than no answer here. Keep the same warm, plain voice."
)


def research(query):
    # answer a factual question with web search, grounded, never fabricated. opt-in
    # (same key as the mirror-self). raises on failure so the caller can say so
    # honestly rather than invent something.
    import anthropic
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=os.environ.get(MODEL_ENV, DEFAULT_MODEL),
        max_tokens=700,
        system=_RESEARCH_SYSTEM,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        messages=[{"role": "user", "content": query}],
    )
    out = "\n".join(b.text for b in message.content
                    if getattr(b, "type", None) == "text" and b.text).strip()
    if not out:
        raise RuntimeError("no answer from the model")
    return out


_DISTILL_SYSTEM = (
    "You read a short conversation between a person and the companion they built. "
    "Pull out at most two durable facts worth remembering about the person's life - "
    "an ongoing situation, a person who matters, something that helps or hurts them, "
    "a goal. NOT passing moods, NOT anything you are unsure about. Write each as a "
    "short phrase under eight words, no quotes, no names you weren't given. Prefix each "
    "with its kind from: weight, lift, person, goal, note. One per line, like "
    "'weight: thesis is hanging over them'. If there is nothing durable, reply NONE."
)


def distill_facts(history):
    # turn a finished thread into a fact or two for the portrait - short distilled
    # phrases, never the transcript. raises on failure so the caller just skips it.
    import anthropic
    client = anthropic.Anthropic()
    convo = "\n".join(f"{'them' if role == 'you' else 'her'}: {content}"
                      for role, content, *_ in history if role in ("you", "her"))
    message = client.messages.create(
        model=os.environ.get(MODEL_ENV, DEFAULT_MODEL),
        max_tokens=120,
        system=_DISTILL_SYSTEM,
        messages=[{"role": "user", "content": convo}],
    )
    out = next((b.text for b in message.content if b.type == "text"), "").strip()
    facts = []
    for line in out.splitlines():
        line = line.strip().lstrip("-•").strip()
        if not line or line.upper() == "NONE":
            continue
        kind, _, txt = line.partition(":")
        kind, txt = kind.strip().lower(), txt.strip()
        if not txt:
            kind, txt = "note", line
        facts.append({"kind": kind, "text": txt})
    return facts[:2]
