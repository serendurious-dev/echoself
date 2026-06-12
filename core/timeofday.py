"""what part of the day it is - for *this* user, on their machine, in their time.

no assumption that night means the same hour for everyone; we read the local
clock. learning a user's real rhythm (when they actually show up, when they tend
to be low) belongs to the daemon and the portrait - this is the honest baseline."""

import datetime

# the day, in the chunks a person actually feels them as. the boundaries are
# soft on purpose - "late" is a mood as much as a clock reading.
PARTS = ("deep_night", "early_morning", "morning", "afternoon", "evening", "night")


def daypart(now=None):
    h = (now or datetime.datetime.now()).hour
    if h < 5:
        return "deep_night"
    if h < 8:
        return "early_morning"
    if h < 12:
        return "morning"
    if h < 17:
        return "afternoon"
    if h < 21:
        return "evening"
    return "night"


def is_late(now=None):
    # the hours where a check-in should soften, not chirp
    return daypart(now) in ("deep_night", "night")
