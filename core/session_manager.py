"""Session manager — the spine of a daily session.

Orchestrates the three phases:
  1. Mood capture (one word, one number — minimal friction)
  2. Pattern check: Dark Days Protocol trigger, or narrative/learning session
  3. Save & reflect: update logs, recalculate Echo Distance, check milestones
     (weekly Mirror Report, monthly Letters)

Reads/writes: data/echo_log.csv, data/learning_log.csv
"""

# Implementation arrives in Layer 1.
