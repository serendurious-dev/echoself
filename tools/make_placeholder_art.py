"""generate a placeholder art pack so the layered-art pipeline can be seen and
tested without real art.

these are flat shapes, deliberately plain - they only prove the socket works:
the layers stack, the eyes blink, the mouth changes with the expression, every
layer breathes on its own beat. drop a real CC0 pack in to replace them, same
folder layout and manifest (see characters/art/README.md).

    python tools/make_placeholder_art.py        # writes characters/art/_placeholder/
"""

import os
import json

import pygame

FRAME = (400, 520)
SKIN  = (240, 213, 192)
HAIR  = (110, 90, 78)
HAIRD = (78, 62, 54)
OUT   = (94, 140, 128)
INK   = (44, 38, 40)


def _surf():
    return pygame.Surface(FRAME, pygame.SRCALPHA)


def write_placeholder_pack(dest):
    os.makedirs(dest, exist_ok=True)
    if not pygame.get_init():
        pygame.init()
    cx, hy = FRAME[0] // 2, 150

    layers = {}

    s = _surf()                                            # back_hair
    pygame.draw.ellipse(s, HAIRD, (cx - 78, hy - 78, 156, 200))
    layers["back_hair.png"] = s

    s = _surf()                                            # body
    pygame.draw.polygon(s, OUT, [(cx - 70, 250), (cx + 70, 250),
                                 (cx + 96, 512), (cx - 96, 512)])
    pygame.draw.circle(s, OUT, (cx - 64, 262), 30)
    pygame.draw.circle(s, OUT, (cx + 64, 262), 30)
    layers["body.png"] = s

    s = _surf()                                            # head
    pygame.draw.ellipse(s, SKIN, (cx - 58, hy - 64, 116, 140))
    pygame.draw.polygon(s, SKIN, [(cx - 16, 232), (cx + 16, 232), (cx + 10, 252), (cx - 10, 252)])
    layers["head.png"] = s

    s = _surf()                                            # eyes_open
    for dx in (-26, 26):
        pygame.draw.ellipse(s, (250, 248, 244), (cx + dx - 16, hy - 8, 32, 22))
        pygame.draw.circle(s, (90, 130, 150), (cx + dx, hy + 3), 8)
        pygame.draw.circle(s, INK, (cx + dx, hy + 3), 4)
    layers["eyes_open.png"] = s

    s = _surf()                                            # eyes_closed
    for dx in (-26, 26):
        pygame.draw.line(s, INK, (cx + dx - 14, hy + 4), (cx + dx + 14, hy + 4), 3)
    layers["eyes_closed.png"] = s

    s = _surf()                                            # mouth_neutral
    pygame.draw.line(s, (150, 90, 92), (cx - 14, hy + 46), (cx + 14, hy + 46), 3)
    layers["mouth_neutral.png"] = s

    s = _surf()                                            # mouth_happy
    pygame.draw.arc(s, (150, 90, 92), (cx - 18, hy + 34, 36, 24), 3.34, 6.08, 3)
    layers["mouth_happy.png"] = s

    s = _surf()                                            # mouth_open
    pygame.draw.ellipse(s, (140, 70, 74), (cx - 12, hy + 40, 24, 18))
    layers["mouth_open.png"] = s

    s = _surf()                                            # front_hair
    pygame.draw.polygon(s, HAIR, [(cx - 60, hy + 6), (cx - 50, hy - 62),
                                  (cx + 54, hy - 62), (cx + 62, hy + 6),
                                  (cx + 30, hy - 26), (cx - 6, hy - 16), (cx - 34, hy - 28)])
    layers["front_hair.png"] = s

    for name, surface in layers.items():
        pygame.image.save(surface, os.path.join(dest, name))

    manifest = {
        "name": "Placeholder",
        "note": "Plain placeholder shapes - replace with a real CC0 pack. See characters/art/README.md.",
        "feet": [0.5, 0.99],
        "layers": [
            {"image": "back_hair.png",     "z": 0, "motion": "hair"},
            {"image": "body.png",          "z": 1, "motion": "body"},
            {"image": "head.png",          "z": 2, "motion": "head"},
            {"image": "eyes_open.png",     "z": 3, "motion": "head", "eyes": "open"},
            {"image": "eyes_closed.png",   "z": 3, "motion": "head", "eyes": "closed"},
            {"image": "mouth_neutral.png", "z": 4, "motion": "head", "mouth": "neutral"},
            {"image": "mouth_happy.png",   "z": 4, "motion": "head", "mouth": "happy"},
            {"image": "mouth_open.png",    "z": 4, "motion": "head", "mouth": "open"},
            {"image": "front_hair.png",    "z": 5, "motion": "head"},
        ],
    }
    with open(os.path.join(dest, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest


if __name__ == "__main__":
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out  = os.path.join(here, "characters", "art", "_placeholder")
    write_placeholder_pack(out)
    print("wrote", out)
    print("to see it: set a character's visual.art to '_placeholder' and run python main.py")
