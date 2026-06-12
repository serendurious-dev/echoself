"""dev tool: render the character expression sheet to a preview png."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from character.renderer import Character, gentle_guide
from visual.worlds import vgradient

NAMES = ["neutral", "happy", "thinking", "drift"]
PANEL = (400, 620)

sheet = pygame.Surface((PANEL[0] * len(NAMES), PANEL[1]))
font  = pygame.font.Font(None, 28)

for i, name in enumerate(NAMES):
    panel = vgradient(PANEL, (18, 24, 44), (64, 54, 96))
    who   = Character(gentle_guide(), pos=(PANEL[0] // 2, 540), height=380)
    who.set_expression(name)
    for _ in range(220):            # let the expression settle and the breath move
        who.update(0.016)
    who._blink_phase = None         # eyes open for the photo
    who.draw(panel)
    panel.blit(font.render(name, True, (230, 230, 230)), (16, PANEL[1] - 40))
    sheet.blit(panel, (i * PANEL[0], 0))

pygame.image.save(sheet, "_preview_character.png")
print("saved _preview_character.png")
