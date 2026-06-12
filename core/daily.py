"""the daily check-in: one word, one number - the only thing EchoSelf asks directly."""

import pygame

from core import session_manager, echo_distance
from core.echo_builder import _Stage


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
