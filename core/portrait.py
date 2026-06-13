"""what she remembers about you, between sittings - the portrait.

not raw transcripts (the words die with the sitting), but distilled facts she can
hold - what weighs on you, what lifts you, the people, the patterns. one local file
you can open, read, and delete from; --export and --forget sweep it like the rest.
nothing here is hidden from you, nothing leaves the machine.

how facts get in: patterns come from the emotion rhythm offline (no words
needed - "weekends sit heavier" falls right out of the log). real content facts -
the thesis, your sister - only come from the model when you've turned it on,
because the offline floor can't honestly pull them from text without guessing."""

import re
import datetime

from core import datastore

PORTRAIT_FILE = "portrait.json"

# the kinds of thing worth keeping. small and human, not a schema for its own sake.
KINDS = ("weight", "lift", "person", "goal", "pattern", "note")

# the heavy feelings, for reading patterns out of the emotion log
_HEAVY = ("sadness", "anger", "fear", "loneliness", "shame")

# patterns are recomputed from fresh data, so they age out fast; a fact she
# pulled from a conversation lingers longer; something you wrote yourself stays
# until you remove it.
_STALE_DAYS = {"pattern": 21, "note": 45, "person": 90, "weight": 45,
               "lift": 90, "goal": 120}


def load():
    p = datastore.load_json(PORTRAIT_FILE, default={"facts": []}) or {"facts": []}
    p.setdefault("facts", [])
    return p


def save(p):
    datastore.save_json(PORTRAIT_FILE, p)


def _norm(text):
    # for dedup: lowercase, collapse spaces, drop trailing punctuation
    return re.sub(r"\s+", " ", text.strip().lower()).rstrip(".!?,")


def _today(when=None):
    when = when or datetime.date.today()
    if isinstance(when, datetime.datetime):
        when = when.date()
    return when.isoformat()


def remember(text, kind="note", source="you", when=None):
    # add a fact, or refresh one she already holds. refreshing bumps its weight
    # and its last-seen, so the things that keep coming up rise to the top.
    text = " ".join(text.split())
    if not text:
        return None
    if kind not in KINDS:
        kind = "note"
    p   = load()
    day = _today(when)
    key = _norm(text)
    for f in p["facts"]:
        if _norm(f["text"]) == key:
            f["last_seen"] = day
            f["weight"]    = round(min(3.0, f.get("weight", 1.0) + 0.5), 2)
            if kind != "note":
                f["kind"] = kind
            save(p)
            return f
    fact = {"id": _new_id(p), "kind": kind, "text": text, "source": source,
            "first_seen": day, "last_seen": day, "weight": 1.0}
    p["facts"].append(fact)
    save(p)
    return fact


def _new_id(p):
    used = {f.get("id") for f in p["facts"]}
    n = 1
    while f"f{n}" in used:
        n += 1
    return f"f{n}"


def forget(fact_id):
    p = load()
    before = len(p["facts"])
    p["facts"] = [f for f in p["facts"] if f.get("id") != fact_id]
    save(p)
    return len(p["facts"]) < before


def clear():
    save({"facts": []})


def _is_stale(fact, when=None):
    if fact.get("source") == "you":
        return False                       # your own words stay until you delete them
    try:
        last = datetime.date.fromisoformat(fact["last_seen"])
    except (KeyError, ValueError):
        return False
    age = (datetime.date.fromisoformat(_today(when)) - last).days
    return age > _STALE_DAYS.get(fact.get("kind", "note"), 45)


def facts(when=None):
    # the live portrait: stale things pruned, the rest ordered so the strongest,
    # most recent facts come first. pruning is written back, so it self-cleans.
    p     = load()
    fresh = [f for f in p["facts"] if not _is_stale(f, when)]
    if len(fresh) != len(p["facts"]):
        p["facts"] = fresh
        save(p)
    return sorted(fresh, key=lambda f: (f.get("weight", 1.0), f.get("last_seen", "")),
                  reverse=True)


# -- patterns from the emotion rhythm (offline, no words) ----------------------

def _emotion_rows():
    return datastore.read_csv("conversation.csv")


def refresh_patterns(when=None):
    # recompute the kind="pattern" facts from the recent emotion log and replace
    # the old ones. this is the offline portrait: she notices the shape of how
    # you've been, without needing to keep a single thing you said.
    rows = _emotion_rows()[-60:]
    p = load()
    p["facts"] = [f for f in p["facts"] if f.get("kind") != "pattern"]
    save(p)

    found = []

    recent = rows[-20:]
    if len(recent) >= 6:
        counts = {}
        for r in recent:
            counts[r["emotion"]] = counts.get(r["emotion"], 0) + 1
        for emo in _HEAVY:
            if counts.get(emo, 0) / len(recent) >= 0.4:
                found.append(f"{emo} has been around a lot lately")

    weekend, weekday = [], []
    for r in rows:
        if r["emotion"] not in _HEAVY:
            continue
        try:
            d = datetime.date.fromisoformat(r["date"])
            i = float(r.get("intensity") or 0)
        except (ValueError, KeyError):
            continue
        (weekend if d.weekday() >= 5 else weekday).append(i)
    if len(weekend) >= 3 and len(weekday) >= 3:
        if sum(weekend) / len(weekend) - sum(weekday) / len(weekday) >= 0.2:
            found.append("weekends seem to sit heavier than weekdays")

    for text in found:
        remember(text, kind="pattern", source="pattern", when=when)
    return found


# -- the gentle opener hint ----------------------------------------------------

def opener_hint(when=None):
    # the one fresh thing most worth checking on first - what's weighing on them,
    # or what they're reaching for. only recent, only the heavy/important kinds,
    # so she leads with care, not cleverness.
    day = datetime.date.fromisoformat(_today(when))
    best = None
    for f in facts(when):
        if f.get("kind") not in ("weight", "goal"):
            continue
        try:
            age = (day - datetime.date.fromisoformat(f["last_seen"])).days
        except (KeyError, ValueError):
            continue
        if age <= 10 and (best is None or f["weight"] > best["weight"]):
            best = f
    return best
