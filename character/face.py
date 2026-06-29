"""render her to a PNG so a web or desktop frontend can show the SAME character the
pygame window draws - one engine, one source of truth for her face. no second drawing
in javascript that would drift from the real one.

the api has no window, so we draw offscreen. her expression follows the emotion of the
moment, the same map the window uses (companion.EXPRESSION)."""

import io
import os

# the server has no display - draw to an offscreen buffer.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from core import session_manager
from core import companion
from character.character_builder import spec_from_profile, make_character
from character.renderer import gentle_guide

# the dusk the web ui sits in, so her glow blends into the room instead of a seam.
DUSK = (28, 24, 34)


def _ensure_pygame():
    if not pygame.get_init():
        pygame.init()
    # a painted character loads its layers with convert_alpha(), which needs a display
    # surface to exist. with the dummy driver that's offscreen and invisible. the guard
    # means we never resize a real window if one is somehow already up.
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))


def render_png(emotion="neutral", height=240, bg=DUSK, portrait=True):
    # her, with the expression this feeling calls for, as png bytes. portrait=True crops
    # to head and shoulders, because that's where a feeling actually shows - at the small
    # size a frontend renders her, a full figure would lose the face the read lives in.
    _ensure_pygame()

    profile = session_manager.load_profile()
    spec    = spec_from_profile(profile) if profile else gentle_guide()

    cw, chh = int(height * 0.74), int(height * 1.05)
    who = make_character(spec, pos=(cw // 2, int(chh - 0.015 * height)), height=height)
    who.set_expression(companion.EXPRESSION.get(emotion, "neutral"))

    # this is a still frame, not an animation - settle the expression at once so she
    # isn't caught mid-change. (the painted ArtCharacter has no expr to settle.)
    if hasattr(who, "expr") and hasattr(who, "target"):
        who.expr = dict(who.target)

    surface = pygame.Surface((cw, chh))
    surface.fill(bg)
    who.draw(surface)

    if portrait:
        # head and shoulders. the figure is centered, so keep full width, top slice.
        surface = surface.subsurface((0, 0, cw, int(chh * 0.46))).copy()

    buf = io.BytesIO()
    pygame.image.save(surface, buf, "face.png")
    return buf.getvalue()
