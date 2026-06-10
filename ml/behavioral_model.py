"""ML brain — behavioral state classification (scikit-learn).

Passive signals only: response speed, pause patterns, session length, time of
day, quiz accuracy trends, answer length/specificity, completion rate, topic
avoidance, Drift Mode timing. Direct questions are avoided by design — people
hide their real state or report what sounds acceptable. Behavior is honest.

Classifies each session into one of five states:
    Flowing   — high energy, genuinely engaged, absorbing well
    Pushing   — trying hard, struggling despite effort
    Drifting  — low energy, present but passive
    Avoiding  — has the energy, circling away from what needs work
    Fading    — withdrawing, responses shortening, thinking of stopping

Cold start: pretrained on synthetic behavioral archetypes (archetypes.py),
then retrained incrementally each session on the real user's data.

Reads: data/echo_log.csv, data/learning_log.csv
Writes: data/user_model.json
"""

# Implementation arrives in Layer 2.
