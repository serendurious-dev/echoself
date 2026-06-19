"""a safety plan - yours, written when you're okay, for when you're not.

a gentle take on the Stanley-Brown Safety Planning Intervention (a real
suicide-prevention tool): your own warning signs, what helps you, your reasons,
and who you can reach. it lives in the data dir like everything else (so --export
and --forget cover it), it's never read by anything but you, and it's never sent
anywhere or shared. she only ever surfaces it, gently, in a hard moment - the
crisis lines for your region get added underneath automatically."""

from core import datastore

PLAN_FILE = "safety_plan.json"

# the sections, in the order they're walked through, each with its prompt
SECTIONS = [
    ("warning_signs", "the signs a hard moment is coming - thoughts, moods, situations"),
    ("what_helps",    "things that have helped before, even a little"),
    ("reasons",       "reasons to stay, things that matter, people you'd come back for"),
    ("people",        "people you could reach - a name, a number, anyone"),
]
_KEYS = [k for k, _ in SECTIONS]


def _blank():
    return {k: [] for k in _KEYS}


def load():
    saved = datastore.load_json(PLAN_FILE, default=None)
    plan  = _blank()
    if isinstance(saved, dict):
        for k in _KEYS:
            if isinstance(saved.get(k), list):
                plan[k] = [str(x) for x in saved[k]]
    return plan


def save(plan):
    datastore.save_json(PLAN_FILE, {k: plan.get(k, []) for k in _KEYS})
    return plan


def add(section, text):
    text = (text or "").strip()
    if section not in _KEYS or not text:
        return load()
    plan = load()
    plan[section].append(text)
    return save(plan)


def remove(section, index):
    plan = load()
    if section in _KEYS and 0 <= index < len(plan[section]):
        plan[section].pop(index)
        save(plan)
    return plan


def has_content(plan=None):
    plan = plan if plan is not None else load()
    return any(plan.get(k) for k in _KEYS)


def summary(region=None):
    # the plan as plain text, with the crisis lines for the region underneath.
    # only the sections you actually filled in show up.
    from core import crisis
    plan  = load()
    parts = []
    for key, prompt in SECTIONS:
        items = plan.get(key, [])
        if items:
            parts.append(prompt + ":\n" + "\n".join(f"  - {x}" for x in items))
    body = "\n\n".join(parts) if parts else "(nothing written yet)"
    lines = "\n".join(crisis.resources_for(region))
    return f"{body}\n\nand if it gets to be too much, real people who can help:\n{lines}"
