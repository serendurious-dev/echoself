"""Quiz engine — in-world questions, hints, and spaced repetition memory.

Renders lesson quizzes in the glowing panel and feeds every answer event to
the expression engine (live reactions) and the behavioral model (passive
signals). A progressive hint system reveals three hints before the answer.

Character memory: questions the user missed return days later, in the
character's voice — "You missed this one before. Try it now." Pedagogically
this is spaced repetition; emotionally, it is the character remembering.
"""

# Implementation arrives in Layer 1; spaced repetition in Layer 2.
