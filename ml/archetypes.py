"""synthetic behavioral archetypes - the cold-start training set, plus a heuristic teacher."""

import random

STATES   = ["Flowing", "Pushing", "Drifting", "Avoiding", "Fading"]
# the seventh signal, valence, is how the day *felt* - read from the conversations,
# not the studying. it's how the inner world learns you from how you talk, not just
# how you work. 0 = heavy, 1 = light; a day with no talk sits neutral at 0.6.
FEATURES = ["accuracy", "avg_duration", "hints_rate", "events", "lessons_done",
            "gap_days", "valence"]

# (mean, spread) per feature, per state. the shapes matter, not the decimals.
# valence has wide spreads on purpose - it nudges the read, it doesn't rule it.
_PROFILES = {
    #             accuracy     duration     hints       events      lessons     gap          valence
    "Flowing":  [(0.85, 0.10), (14.0, 5.0), (0.2, 0.2), (12.0, 4.0), (1.6, 0.7), (1.0, 0.7), (0.74, 0.18)],
    "Pushing":  [(0.45, 0.12), (38.0, 9.0), (1.6, 0.5), (10.0, 3.0), (0.7, 0.5), (1.2, 0.8), (0.50, 0.20)],
    "Drifting": [(0.60, 0.15), (30.0, 8.0), (0.6, 0.4), (4.0, 1.8),  (0.3, 0.4), (2.0, 1.0), (0.52, 0.20)],
    "Avoiding": [(0.75, 0.12), (12.0, 4.0), (0.3, 0.3), (3.0, 1.5),  (0.2, 0.3), (4.5, 1.5), (0.46, 0.20)],
    "Fading":   [(0.40, 0.15), (45.0, 12.0), (0.4, 0.4), (2.0, 1.0), (0.1, 0.2), (6.5, 2.0), (0.34, 0.18)],
}


def synthetic_sessions(per_state=40, seed=7):
    # the pretraining set. seeded, so the model starts from the same place on
    # every machine - reproducibility is part of being honest about this.
    rng = random.Random(seed)
    rows, labels = [], []
    for state in STATES:
        for _ in range(per_state):
            row = []
            for (mean, spread) in _PROFILES[state]:
                row.append(max(0.0, rng.gauss(mean, spread)))
            row[0]  = min(1.0, row[0])     # accuracy stays a share
            row[-1] = min(1.0, row[-1])    # so does valence
            rows.append(row)
            labels.append(state)
    return rows, labels


def heuristic_label(row):
    # the bootstrap teacher: plain rules that pseudo-label the user's own past
    # sessions so the classifier can learn from their history too. the rules
    # mirror the archetype shapes on purpose. valence (row[6]) is left to the
    # classifier - the heuristic reads the six behavioral signals.
    accuracy, duration, hints, events, lessons, gap = row[:6]
    if gap >= 5 and events <= 4:
        return "Fading"
    if gap >= 3 and events <= 5 and lessons < 1:
        return "Avoiding"
    if events <= 5 and lessons < 1:
        return "Drifting"
    if accuracy < 0.55 or hints >= 1.2:
        return "Pushing"
    return "Flowing"
