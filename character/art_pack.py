"""layered art characters - the socket real art plugs into.

a character can be drawn two ways. the procedural one in renderer.py is the
fallback, drawn entirely by code. this is the other one: stacked PNG layers
composited and animated the way a visual-novel app does it, so painted art -
a clean open-licensed pack, or your own - can be the body instead.

an art pack is a folder under characters/art/<id>/ with a manifest.json and
its layer images. the manifest lists layers back-to-front, each tagged with how
it moves (body / head / hair) and, where it matters, which eye state or mouth
shape it is. the engine picks the right eyes for the blink and the right mouth
for the expression, and bobs each layer on its own beat so flat images breathe.
the manifest format is documented in characters/art/README.md.

ArtCharacter matches the procedural Character's interface exactly - same
__init__, set_expression, update, draw, .pos, .h, .spec - so the rest of the
app never knows or cares which one it got.
"""

import os
import json
import math
import random

import pygame

ART_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "characters", "art")

# the mouth shape each expression wants. the pack supplies whatever shapes it
# has; we fall back to neutral, then to whatever exists.
_MOUTH = {"neutral": "neutral", "happy": "happy", "patient": "happy",
          "thinking": "neutral", "celebrating": "open", "drift": "neutral"}


def pack_dir(art_id):
    # the folder for an art id, or None if it has no manifest
    if not art_id:
        return None
    path = os.path.join(ART_DIR, art_id)
    return path if os.path.isfile(os.path.join(path, "manifest.json")) else None


class ArtCharacter:

    def __init__(self, spec, pos=(640, 540), height=300, art_dir=None):
        self.spec = spec
        self.pos  = pos
        self.h    = height
        art_dir   = art_dir or pack_dir(getattr(spec, "art", None))
        if art_dir is None:
            raise FileNotFoundError("no art pack for this character")

        with open(os.path.join(art_dir, "manifest.json"), encoding="utf-8") as f:
            self.manifest = json.load(f)
        self.feet = self.manifest.get("feet", [0.5, 0.98])

        self.layers = []
        for layer in sorted(self.manifest["layers"], key=lambda l: l.get("z", 0)):
            img = pygame.image.load(os.path.join(art_dir, layer["image"])).convert_alpha()
            self.layers.append((layer, img))
        self.src_h = self.layers[0][1].get_height() if self.layers else 1

        self.expr_name    = "neutral"
        self.t            = 0.0
        self._blink_phase = None
        self._next_blink  = random.uniform(2.0, 5.0)
        self._has_closed  = any(l.get("eyes") == "closed" for l, _ in self.layers)
        self._mouths      = {l.get("mouth") for l, _ in self.layers if l.get("mouth")}

    # -- same interface as the procedural Character --------------------------

    def set_expression(self, name):
        # validated against the procedural set so the two stay in lockstep
        from character.renderer import EXPRESSIONS
        if name not in EXPRESSIONS:
            raise ValueError(f"unknown expression '{name}'")
        self.expr_name = name

    def update(self, dt):
        self.t += dt
        if self._blink_phase is None:
            self._next_blink -= dt
            if self._next_blink <= 0:
                self._blink_phase = 0.0
        else:
            self._blink_phase += dt / 0.22
            if self._blink_phase >= 1.0:
                self._blink_phase = None
                self._next_blink  = random.uniform(2.0, 5.0)

    # -- layer selection ------------------------------------------------------

    def _blinking(self):
        return self._blink_phase is not None and 0.2 < self._blink_phase < 0.8

    def _mouth_for(self):
        want = _MOUTH.get(self.expr_name, "neutral")
        if want in self._mouths:
            return want
        if "neutral" in self._mouths:
            return "neutral"
        return next(iter(self._mouths), None)

    def _visible(self, layer, mouth):
        eyes = layer.get("eyes")
        if eyes == "closed":
            return self._has_closed and self._blinking()
        if eyes == "open":
            return not (self._has_closed and self._blinking())
        if layer.get("mouth"):
            return layer["mouth"] == mouth
        if "expr" in layer:
            return self.expr_name in layer["expr"]
        return True

    # -- motion: flat layers, each on its own beat = the breathing ------------

    def _offset(self, motion, scale):
        w     = math.tau / 4.2
        sway  = math.sin(self.t * 0.31) * 2.0 * scale
        if motion == "body":
            return (sway * 0.4, -math.sin(self.t * w) * self.h * 0.006)
        if motion == "head":
            return (sway, -math.sin(self.t * w - 0.6) * self.h * 0.008)
        if motion == "hair":
            return (sway * 1.2, -math.sin(self.t * w - 0.9) * self.h * 0.010)
        return (0.0, 0.0)

    def draw(self, surface):
        scale = self.h / self.src_h
        mouth = self._mouth_for()
        # feet of the (unscaled) frame -> where pos is
        fx = self.feet[0] * self.layers[0][1].get_width() * scale
        fy = self.feet[1] * self.src_h * scale
        for layer, img in self.layers:
            if not self._visible(layer, mouth):
                continue
            scaled = pygame.transform.smoothscale(
                img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            ox, oy = self._offset(layer.get("motion", "none"), scale)
            surface.blit(scaled, (int(self.pos[0] - fx + ox), int(self.pos[1] - fy + oy)))
