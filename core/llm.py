"""the optional hybrid brain: Claude writes the companion's reply when a key is
set. offline stays the default and the safety net - this runs only when
ANTHROPIC_API_KEY is present and the anthropic SDK is installed, and it never
sees a crisis message (companion.py handles those before it gets here)."""

import os

MODEL_ENV     = "ECHOSELF_LLM_MODEL"
DEFAULT_MODEL = "claude-opus-4-8"

_SYSTEM = (
    "You are the companion inside EchoSelf - a warm, steady presence the person built "
    "for themselves. The rule is presence over pressure: validate first, never fix, "
    "never shame, never lecture, never give medical or clinical advice. You are a "
    "companion, not a clinician.\n"
    "Right now the emotion under their words reads as '{emotion}', and your stance is "
    "'{stance}'. Answer in one to three short, human sentences - the way a close, calm "
    "friend would. No bullet points, no 'as an AI'. If they ever sound in real danger, "
    "gently urge them toward a real person or a crisis line."
)


def available():
    # only when the user has opted in (a key) and the SDK is installed
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False


def reply(text, emotion, stance):
    # one short companion reply from Claude. raises on any failure so the caller
    # falls back to the offline library - the conversation never breaks.
    import anthropic
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=os.environ.get(MODEL_ENV, DEFAULT_MODEL),
        max_tokens=200,
        system=_SYSTEM.format(emotion=emotion, stance=stance),
        messages=[{"role": "user", "content": text}],
    )
    out = next((b.text for b in message.content if b.type == "text"), "").strip()
    if not out:
        raise RuntimeError("empty reply from the model")
    return out
