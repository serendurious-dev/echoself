"""the daily check-in. it used to be one word and one number - the only thing
EchoSelf asked directly. now she just talks to you ("how was today?"), reads the
mood from the conversation, and logs the number quietly underneath, so the data
layer and the brain keep what they need without a cold form. the old word+number
capture stays below as a fallback."""

from collections import Counter

import pygame

from core import session_manager, echo_distance
from core.echo_builder import _Stage

# a plain word for each read feeling, for the mood log the brain reads
_MOOD_WORD = {
    "joy": "good", "neutral": "okay", "sadness": "low", "anger": "angry",
    "fear": "anxious", "loneliness": "lonely", "shame": "down on myself",
    "overwhelm": "overwhelmed", "guilt": "guilty", "grief": "grieving",
    "numbness": "numb", "crisis": "in the dark",
}


def mood_from_conversation(conv):
    # read the day's mood from what she heard, not from a form. returns (word,
    # score 1-10) or (None, None) if you didn't actually say anything. the score
    # reuses the same emotion->valence the Echo Distance uses, so it all agrees.
    emos = [e for role, _t, e in conv.history if role == "you" and e]
    if not emos:
        return None, None
    dominant = Counter(emos).most_common(1)[0][0]
    valence  = echo_distance._EMO_VALENCE.get(dominant, 0.6)
    score    = max(1, min(10, round(1 + valence * 9)))
    return _MOOD_WORD.get(dominant, "okay"), score


def log_checkin(conv, profile):
    # turn a finished check-in conversation into the day's mood row. if nothing
    # was said, nothing is logged - skipping the check-in is allowed.
    word, score = mood_from_conversation(conv)
    if word is None:
        return None
    session_manager.log_mood(word, score, distances=echo_distance.compute(profile))
    return word, score


def _ask_word(stage, prompt):
    typed = ""
    while True:
        stage.frame()
        for e in pygame.event.get([pygame.KEYDOWN]):
            if e.key == pygame.K_RETURN and typed.strip():
                return typed.strip()
            elif e.key == pygame.K_BACKSPACE:
                typed = typed[:-1]
            elif e.unicode and e.unicode.isprintable() and len(typed) < 24:
                typed += e.unicode
        stage.say(prompt, 0.32)
        cursor = "_" if int(stage.t * 2) % 2 == 0 else " "
        stage.say(typed + cursor, 0.48, stage.mid, color=(214, 222, 234))
        stage.hint("a word for today. enter when ready.")
        pygame.display.flip()


def _ask_number(stage, prompt):
    # one to ten, picked with the arrows so it cannot be fumbled
    value = 5
    while True:
        stage.frame()
        for e in pygame.event.get([pygame.KEYDOWN]):
            if e.key in (pygame.K_LEFT, pygame.K_DOWN):
                value = max(1, value - 1)
            elif e.key in (pygame.K_RIGHT, pygame.K_UP):
                value = min(10, value + 1)
            elif pygame.K_1 <= e.key <= pygame.K_9:
                value = e.key - pygame.K_0
            elif e.key == pygame.K_RETURN:
                return value
        stage.say(prompt, 0.32)
        bar = "  ".join(("[" + str(n) + "]" if n == value else str(n))
                        for n in range(1, 11))
        stage.say(bar, 0.48, stage.mid, color=(214, 222, 234))
        stage.hint("left and right, or a number key. enter when ready.")
        pygame.display.flip()


def capture_mood(screen, clock, profile):
    # the whole check-in. returns the (word, score) it logged.
    stage = _Stage(screen, clock)
    word  = _ask_word(stage, "one word for today.")
    score = _ask_number(stage, "and how heavy or light, one to ten?")
    session_manager.log_mood(word, score, distances=echo_distance.compute(profile))
    return word, score
