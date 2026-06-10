"""the ML brain. sklearn classifier over passive behavioral signals.

signals only, no questions - people hide their real state or report what sounds
acceptable, behavior is honest. response speed, pauses, session length, time of day,
accuracy trends, answer length, completion rate, what gets avoided, when Drift Mode
gets used.

five states out: Flowing, Pushing, Drifting, Avoiding, Fading.

cold start is handled by archetypes.py - pretrain on synthetic archetype sessions,
then re-fit incrementally on the real user every session. session one works, and it
keeps getting more personal.

reads data/echo_log.csv + data/learning_log.csv, writes data/user_model.json
"""

# Layer 2
