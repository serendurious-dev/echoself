"""narrative: the Dark Days Protocol and the Mirror Report.

the arcs and Echo Moments are roadmap. what lives here now is the part that
matters most - the system noticing when someone is having a hard stretch and
easing off, and the weekly letter the ideal self writes back. presence over
pressure is enforced here more than anywhere.
"""

import datetime

from core import session_manager


def dark_days_active(threshold=4, streak=3):
    # a low-mood streak: the last `streak` distinct days all logged at or below
    # `threshold` (out of 10). when this is true, the narrative pauses - no
    # lessons pushed, no prompts, just presence.
    by_day = {}
    for row in session_manager.read_echo_log():
        if row.get("mood_score"):
            by_day[row["date"]] = int(row["mood_score"])   # last entry wins per day
    days = sorted(by_day)[-streak:]
    return len(days) >= streak and all(by_day[d] <= threshold for d in days)


def _ideal_name(profile):
    try:
        return profile["ideal_self"]["name"]
    except (KeyError, TypeError):
        return "your ideal self"


def mirror_report(profile, when=None):
    # a weekly reflection, written in the first person as the ideal self,
    # speaking to the user. it references the real week - moods, showing up,
    # lessons - because being seen accurately is the whole point.
    when    = when or datetime.date.today()
    week    = [r for r in session_manager.read_echo_log()
               if r["date"] >= (when - datetime.timedelta(days=7)).isoformat()]
    name    = _ideal_name(profile)
    you     = (profile or {}).get("your_name", "you")
    days    = len({r["date"] for r in week})
    moods   = [int(r["mood_score"]) for r in week if r.get("mood_score")]
    avg     = sum(moods) / len(moods) if moods else None

    lines = [f"From {name}, at the end of the week.", ""]
    if days == 0:
        lines.append(f"{you}, you did not come this week. That is allowed. I am still here,")
        lines.append("and the week the door stays open is not wasted. Come when you can.")
        return "\n".join(lines)

    lines.append(f"{you}, you showed up {days} day{'s' if days != 1 else ''} this week.")
    if avg is not None and avg <= 4:
        lines.append("The days were heavy - I saw the numbers. And you came anyway,")
        lines.append("which is the harder, braver thing. I am not measuring you against")
        lines.append("a perfect week. I am measuring you against how heavy it was.")
    elif avg is not None and avg >= 7:
        lines.append("There was light in the week - I could feel it in how you answered.")
        lines.append("Hold onto the shape of these days. You will want them later.")
    else:
        lines.append("An ordinary week, and ordinary is not nothing. You kept the thread.")
    lines.append("")
    lines.append("Whatever this next week asks, you do not face it alone. - " + name)
    return "\n".join(lines)
