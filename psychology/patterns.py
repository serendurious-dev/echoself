"""noticing a pattern, gently - never naming a condition.

reads the feeling the recent conversations have carried (only the signal, never
the words) and, when one heavy feeling keeps coming back, offers a soft
observation. if it's really persistent, it leans toward a real person - because a
companion that notices someone struggling for weeks and says nothing isn't being
kind. it names a pattern ('anxiety's come up a lot'), never a diagnosis."""

from collections import Counter

_HEAVY = {"sadness", "fear", "loneliness", "shame", "overwhelm", "guilt", "grief", "numbness"}

# how she'd gently name a recurring run of each - a pattern, not a verdict
_NOTICE = {
    "fear":       "anxiety's come up a lot lately",
    "sadness":    "it's been heavy more days than not lately",
    "loneliness": "you've been feeling pretty alone lately",
    "shame":      "you've been hard on yourself a lot lately",
    "overwhelm":  "it's felt like too much, a lot of days lately",
    "guilt":      "you've been carrying blame a lot lately",
    "grief":      "the missing has been close a lot lately",
    "numbness":   "things have felt flat and far away a lot lately",
}


def recent(limit=30):
    from core import companion
    return [r["emotion"] for r in companion.recent_emotions(limit)]


def notice(limit=30, threshold=4):
    # returns a gentle observation when one heavy feeling recurs enough, else None.
    # `persistent` (twice the threshold) tips it toward urging real human help.
    counts = Counter(e for e in recent(limit) if e in _HEAVY)
    if not counts:
        return None
    emo, n = counts.most_common(1)[0]
    if n < threshold:
        return None
    persistent = n >= threshold * 2
    tail = (" if it keeps sitting this heavy, please let a real person in - someone you trust, "
            "or a professional. you shouldn't have to carry it this long alone."
            if persistent else
            " no pressure - just something i noticed. here if you want to talk about it.")
    return {"emotion": emo, "count": n, "persistent": persistent,
            "line": _NOTICE.get(emo, "that feeling's come up a lot lately") + "." + tail}
