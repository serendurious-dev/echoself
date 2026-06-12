"""the Letter System: a monthly letter from the ideal self, saved as plain .txt."""

import os
import datetime

from core import session_manager, datastore


def _dir():
    path = os.path.join(datastore.DATA_DIR, "letters")
    os.makedirs(path, exist_ok=True)
    return path


def _ideal(profile):
    try:
        return profile["ideal_self"]["name"]
    except (KeyError, TypeError):
        return "the one you're becoming"


def month_key(when=None):
    return (when or datetime.date.today()).strftime("%Y-%m")


def letter_path(when=None):
    return os.path.join(_dir(), f"letter_{month_key(when)}.txt")


def due(when=None):
    # a new letter is due once a month, when this month's does not exist yet
    return not os.path.exists(letter_path(when))


def compose(profile, when=None):
    # the ideal self's monthly letter, from the month the logs remember
    when  = when or datetime.date.today()
    since = (when - datetime.timedelta(days=30)).isoformat()
    rows  = [r for r in session_manager.read_echo_log() if r["date"] >= since]
    name  = _ideal(profile)
    you   = (profile or {}).get("your_name", "you")
    days  = len({r["date"] for r in rows})
    moods = [int(r["mood_score"]) for r in rows if r.get("mood_score")]
    avg   = sum(moods) / len(moods) if moods else None

    lines = [f"To {you}, at the turn of the month.", "",
             f"It's me - {name}. The one you're walking toward.", ""]
    if days == 0:
        lines += ["This month was quiet between us. You didn't come much, and I want you to",
                  "hear this plainly: that is not a failure. Some months are for surviving,",
                  "and surviving counts. I'm not going anywhere. The door stays open."]
    else:
        lines.append(f"You came {days} day{'s' if days != 1 else ''} this month. I counted "
                     f"every one.")
        if avg is not None and avg <= 4:
            lines += ["They were heavy days, mostly - I saw the numbers, and I'm not going to",
                      "pretend they were light. But you kept showing up into the weight, and",
                      "that is the bravest, least-noticed thing a person can do."]
        elif avg is not None and avg >= 7:
            lines += ["There was real light in the month. I felt it in how you answered, in the",
                      "days you stayed longer than you had to. Remember this stretch. You'll",
                      "want its shape on the harder months."]
        else:
            lines += ["An ordinary month, and I've come to love ordinary - it's where most of a",
                      "life is actually lived. You held the thread. That's the whole job."]
    lines += ["",
              "I'm not ahead of you. I'm just a little further down the same road, looking",
              "back, telling you the path goes somewhere. Keep coming.", "",
              f"- {name}", "",
              "-" * 60,
              "(your letter back, whenever you're ready:)", ""]
    return "\n".join(lines)


def write_monthly(profile, when=None):
    # generate and save this month's letter if it isn't there yet. returns the path.
    path = letter_path(when)
    if not os.path.exists(path):
        datastore.atomic_write_text(path, compose(profile, when))
    return path


def append_reply(text, when=None):
    # the user's letter back, saved beneath the ideal self's
    path = letter_path(when)
    existing = read(path) if os.path.exists(path) else ""
    datastore.atomic_write_text(path, existing + "\n" + text.rstrip() + "\n")


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def all_letters():
    # (month_key, path), newest first
    out = []
    for name in sorted(os.listdir(_dir()), reverse=True):
        if name.startswith("letter_") and name.endswith(".txt"):
            out.append((name[len("letter_"):-len(".txt")], os.path.join(_dir(), name)))
    return out
