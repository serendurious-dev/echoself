"""Synthetic behavioral archetypes — solving the cold-start problem honestly.

A classifier with no training data is a guess. Before the first real session,
we generate labeled synthetic sessions describing how each of the five states
plausibly looks in the behavioral features (a Fading user's answers shorten;
their pauses grow; their sessions compress). The model pretrains on these
archetypes, then incrementally re-fits on the real user every session —
so personal accuracy grows over time while session one still works.
"""

# Implementation arrives in Layer 2.
