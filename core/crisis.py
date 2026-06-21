"""crisis safety - deterministic, offline, never the model's call.

when a message reads as a crisis the companion stops everything and points to
real human help, with the right lines for where the person is. this is plain
code on purpose: safety must never depend on a key, a network, or a model.
detection lives in core/emotion (is_crisis); this is what she says and who she
points to. sources and the reasoning are in ETHICS.md."""

# the staying-present care, said the same way everywhere, before any number
_CARE = (
    "I'm really glad you told me, and I'm staying right here with you.\n"
    "What you're carrying sounds like more than anyone should carry alone - and I'm a "
    "program, not a person who can keep you safe tonight. Please reach out to someone who "
    "can, right now: a crisis line, a doctor, or someone you trust.")

_CLOSE = "You deserve a real voice on the other end. I'll be here when you come back."

# region -> the crisis lines for that country. short and current; add freely.
RESOURCES = {
    "KR": ["South Korea: call 109 (suicide prevention), or 1393."],
    "US": ["US: call or text 988 (Suicide & Crisis Lifeline)."],
    "CA": ["Canada: call or text 988."],
    "GB": ["UK & Ireland: call 116 123 (Samaritans), free, any time."],
    "IN": ["India: call 14416 (Tele-MANAS), or 9152987821 (iCall)."],
    "AU": ["Australia: call 13 11 14 (Lifeline)."],
    "BD": ["Bangladesh: call 09612-119911 (Kaan Pete Roi)."],
    "JP": ["Japan: call 0570-064-556 (Yorisoi), or 03-5774-0992 (TELL)."],
}

# always shown, after any local line, so help is reachable from anywhere
_INTERNATIONAL = [
    "Anywhere: findahelpline.com lists a free, confidential line for your country.",
    "If you're in immediate danger, contact your local emergency number.",
]

DEFAULT_REGION = "KR"

# the regions the settings screen cycles through, and their plain names
REGIONS = ["KR", "US", "CA", "GB", "IN", "AU", "BD", "JP"]
_NAMES = {"KR": "South Korea", "US": "United States", "CA": "Canada",
          "GB": "UK & Ireland", "IN": "India", "AU": "Australia",
          "BD": "Bangladesh", "JP": "Japan"}


def region_name(code):
    return _NAMES.get((code or "").upper(), code)


def next_region(code):
    # the next region in the cycle, wrapping around
    try:
        i = REGIONS.index((code or DEFAULT_REGION).upper())
    except ValueError:
        i = -1
    return REGIONS[(i + 1) % len(REGIONS)]


def resources_for(region=None):
    # the local lines (falling back to none if the region's unknown) plus the
    # international ones, which are always there
    region = (region or DEFAULT_REGION).upper()
    return RESOURCES.get(region, []) + _INTERNATIONAL


def reply(region=None):
    # the full crisis message: care first, then the lines, then a way back
    lines = "\n".join(resources_for(region))
    return f"{_CARE}\n{lines}\n{_CLOSE}"
