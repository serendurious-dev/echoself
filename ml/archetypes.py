"""synthetic archetypes, the honest answer to the cold-start problem.

a classifier with no data is a guess. so before the first real session we generate
labeled synthetic sessions for each of the five states - a Fading user's answers
shorten, their pauses grow, their sessions compress. the model pretrains on these,
then the real user's data takes over incrementally.
"""

# Layer 2
