"""the don't-give-up layer. reads learning_log into per-topic mastery (not just
done/not-done), the next single step, a momentum that doesn't shame a break, and a
welcome back after time away."""

import datetime

from learning import codepath, progress_tracker

# the languages CodePath teaches. python is the deep one (lessons + real coding
# challenges run in your own editor); c / c++ / java are quiz-based intro tracks.
TRACKS = [("python", "Python"), ("c", "C"), ("cpp", "C++"), ("java", "Java")]

# a human title for each cluster, so the dashboard reads like topics, not numbers
_CLUSTER_TITLES = {
    ("python", 1): "the basics",
    ("python", 2): "flow & functions",
    ("python", 3): "structures & classes",
    ("c", 1):    "C basics",
    ("cpp", 1):  "C++ basics",
    ("java", 1): "Java basics",
}

_AWAY_DAYS = 3        # the gap after which she gently says "welcome back"


def active_track():
    from core import settings
    return settings.get("learning_track")


def track_name(track):
    return dict(TRACKS).get(track, track)


def _today():
    return datetime.date.today()


def gap_days(track="python"):
    # days since the last time you did anything in this track, or None if never
    dates = [r["date"] for r in progress_tracker.read_learning_log() if r["track"] == track]
    if not dates:
        return None
    return (_today() - datetime.date.fromisoformat(max(dates))).days


def _clusters(track):
    lessons     = codepath.load_track(track)
    extras      = codepath.load_extras(track)
    done_les    = progress_tracker.completed_lessons(track)     # {(str(cluster), id)}
    done_extras = progress_tracker.completed_extras(track)      # {id}
    out = []
    for c in sorted({l.get("cluster") for l in lessons}):
        cl = [l for l in lessons if l.get("cluster") == c]
        ce = [e for e in extras if e.get("cluster") == c]
        total = len(cl) + len(ce)
        done  = (sum(1 for l in cl if (str(c), l["id"]) in done_les)
                 + sum(1 for e in ce if e["id"] in done_extras))
        out.append({"cluster": c,
                    "title":   _CLUSTER_TITLES.get((track, c), f"cluster {c}"),
                    "done":    done, "total": total,
                    "mastery": (done / total) if total else 0.0})
    return out


def _next_step(track):
    lesson = codepath.next_lesson(track)
    if lesson:
        return {"kind": "lesson", "title": lesson["title"], "id": lesson["id"],
                "cluster": lesson.get("cluster")}
    extra = codepath.next_challenge(track)
    if extra:
        return {"kind": extra.get("kind", "challenge"),
                "title": extra.get("title", extra["id"]), "id": extra["id"],
                "cluster": extra.get("cluster")}
    return {"kind": "done"}


def welcome_back_line(track="python"):
    # the no-guilt return. only after a real gap, and never a word of blame.
    gap = gap_days(track)
    if gap is None or gap < _AWAY_DAYS:
        return None
    return (f"it's been {gap} days - and that's completely okay. no guilt, none. "
            "you came back, and that's the whole thing.")


def report(track=None):
    # the whole picture the dashboard draws and the lesson world reads.
    track = track or active_track()
    clusters = _clusters(track)
    total = sum(c["total"] for c in clusters)
    done  = sum(c["done"] for c in clusters)
    overall = (done / total) if total else 0.0

    nxt = _next_step(track)
    if nxt["kind"] == "done":
        next_line = "you finished the whole track. that happened, and it was you."
    else:
        cr   = next((c for c in clusters if c["cluster"] == nxt.get("cluster")), None)
        left = (cr["total"] - cr["done"]) if cr else None
        if left and left <= 2:
            s = "s" if left != 1 else ""
            next_line = f"you're {left} step{s} from finishing {cr['title']}. closer than it feels."
        else:
            next_line = f"next, just one thing: {nxt['title']}."

    dates = sorted({r["date"] for r in progress_tracker.read_learning_log()
                    if r["track"] == track})
    shown_up = len(dates)
    if shown_up:
        s = "s" if shown_up != 1 else ""
        momentum = f"you've shown up {shown_up} day{s}. every one of them counts."
    else:
        momentum = "this is day one. the best time to start is now."

    return {
        "track":        track,
        "track_name":   track_name(track),
        "clusters":     clusters,
        "overall":      overall,
        "next":         nxt,
        "next_line":    next_line,
        "days_shown_up": shown_up,
        "gap_days":     gap_days(track),
        "welcome_back": welcome_back_line(track),
        "momentum":     momentum,
    }
