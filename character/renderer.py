"""procedural character renderer.

a soft glowing semi-humanoid figure out of layered light. no PNGs, no sprite
sheets - the character is source code, breathing.

how it works: every part of the figure (body column, head, eyes, the chest
symbol, the motes drifting around) is a radial glow sprite, and everything is
composited additively onto a black canvas, then the canvas is added onto the
sky. light accumulates the way real light does, so the parts melt into each
other instead of looking like pasted circles.

the figure is parameters all the way down - palette, form, glow, symbol come
from a personality pack's visual block (characters/*.json) or the custom
builder. expressions are parameter targets the expression engine can drive,
the renderer just eases toward whatever is asked of it.

preview without the rest of the app:  python -m character.renderer
"""

import os
import json
import math
import random

import pygame

PACK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "characters")

# what the expression engine gets to drive. values are targets, the renderer
# eases toward them so nothing ever snaps.
EXPRESSIONS = {
    "neutral":     dict(eye_open=1.00, eye_curve=0.00, glow=1.00, breath=1.00, sway=1.00, motes=1.00, tilt=0.00),
    "happy":       dict(eye_open=0.55, eye_curve=0.80, glow=1.25, breath=1.10, sway=1.00, motes=1.60, tilt=0.12),
    "patient":     dict(eye_open=0.85, eye_curve=0.25, glow=0.90, breath=0.80, sway=0.70, motes=0.80, tilt=0.20),
    "thinking":    dict(eye_open=0.70, eye_curve=0.00, glow=0.95, breath=1.00, sway=0.40, motes=0.70, tilt=-0.25),
    "celebrating": dict(eye_open=0.50, eye_curve=1.00, glow=1.50, breath=1.30, sway=1.20, motes=2.40, tilt=0.00),
    "drift":       dict(eye_open=0.60, eye_curve=0.15, glow=0.75, breath=0.65, sway=0.50, motes=0.50, tilt=0.10),
}

FORMS = {"soft": 1.00, "slender": 0.82, "broad": 1.18}   # body width factor


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


class CharacterSpec:
    # the visual identity. built from a personality pack's visual block, or
    # defaults that look decent on a dark sky.

    def __init__(self, palette=None, glow=0.5, form="soft", symbol="circle"):
        self.palette = [hex_to_rgb(c) if isinstance(c, str) else tuple(c)
                        for c in (palette or ["#7FB5A8", "#E8DCC8", "#4A6670"])]
        self.glow    = glow
        self.form    = form
        self.symbol  = symbol

    @classmethod
    def from_pack(cls, path):
        # a missing or broken pack should never kill the app, you just get the default figure
        try:
            with open(path, encoding="utf-8") as f:
                visual = json.load(f).get("visual", {})
            return cls(palette=visual.get("palette"),
                       glow=visual.get("glow_intensity", 0.5),
                       form=visual.get("form", "soft"),
                       symbol=visual.get("symbol", "circle"))
        except (OSError, ValueError):
            return cls()


class Character:
    # the figure itself. update(dt) moves the breath, the blink, the motes,
    # draw(surface) paints it. pos is where the base of the figure sits.

    def __init__(self, spec=None, pos=(640, 540), height=300):
        self.spec   = spec or CharacterSpec()
        self.pos    = pos
        self.h      = height
        self.expr   = dict(EXPRESSIONS["neutral"])
        self.target = dict(EXPRESSIONS["neutral"])

        self.t            = 0.0
        self._blink_phase = None                       # None = eyes open, else 0..1 through the blink
        self._next_blink  = random.uniform(2.0, 5.0)
        self._cache       = {}                         # glow sprites, keyed by size+color+brightness

        w, h = int(height * 1.7), int(height * 1.35)
        self.canvas = pygame.Surface((w, h))           # plain black, composited additively

        # the motes: little lights that live around the figure
        self.motes = [dict(a=random.uniform(0, math.tau),
                           r=random.uniform(0.30, 0.62) * height,
                           speed=random.uniform(0.08, 0.30) * random.choice((-1, 1)),
                           size=random.randint(2, 4),
                           phase=random.uniform(0, math.tau))
                      for _ in range(14)]

    # -- expressions ---------------------------------------------------------

    def set_expression(self, name):
        if name not in EXPRESSIONS:
            raise ValueError(f"unknown expression '{name}', have: {', '.join(sorted(EXPRESSIONS))}")
        self.target = dict(EXPRESSIONS[name])

    # -- time ----------------------------------------------------------------

    def update(self, dt):
        self.t += dt * self.expr["breath"]

        # ease toward the target expression, never snap
        k = 1.0 - math.exp(-4.0 * dt)
        for key in self.expr:
            self.expr[key] += (self.target[key] - self.expr[key]) * k

        # blinking. eyes close and open in ~0.22s, then a new random wait.
        if self._blink_phase is None:
            self._next_blink -= dt
            if self._next_blink <= 0:
                self._blink_phase = 0.0
        else:
            self._blink_phase += dt / 0.22
            if self._blink_phase >= 1.0:
                self._blink_phase = None
                self._next_blink  = random.uniform(2.0, 5.0)

        for m in self.motes:
            m["a"] += m["speed"] * dt * self.expr["motes"]

    # -- light ---------------------------------------------------------------

    def _glow(self, radius, color, brightness, spread=2.0, focus=2.4):
        # a cached radial gradient sprite. drawn once small, smoothscaled up,
        # so the falloff is soft and building one costs almost nothing.
        # spread = how far the halo reaches past the radius. focus = falloff
        # shape, high is wispy, low is a hard bright core (eyes want low).
        radius = max(2, int(radius))
        key = (radius, color, round(brightness, 2), spread, focus)
        sprite = self._cache.get(key)
        if sprite is None:
            base = pygame.Surface((48, 48))
            for i in range(24, 0, -1):
                f = ((24 - i) / 24.0) ** focus * brightness
                c = (min(255, int(color[0] * f)),
                     min(255, int(color[1] * f)),
                     min(255, int(color[2] * f)))
                pygame.draw.circle(base, c, (24, 24), i)
            size   = max(4, int(radius * 2 * spread))
            sprite = pygame.transform.smoothscale(base, (size, size))
            self._cache[key] = sprite
        return sprite

    def _add(self, sprite, center):
        self.canvas.blit(sprite, (int(center[0] - sprite.get_width() / 2),
                                  int(center[1] - sprite.get_height() / 2)),
                         special_flags=pygame.BLEND_RGB_ADD)

    # -- the figure ----------------------------------------------------------

    def draw(self, surface):
        self.canvas.fill((0, 0, 0))

        h       = self.h
        cw, ch  = self.canvas.get_size()
        cx      = cw / 2
        base_y  = ch - h * 0.08
        breath  = math.sin(self.t * math.tau / 4.6)
        sway    = math.sin(self.t * 0.31) * self.expr["sway"]
        width   = FORMS.get(self.spec.form, 1.0)
        light   = (0.55 + self.spec.glow * 0.9) * self.expr["glow"]
        body_c, accent_c = self.spec.palette[0], self.spec.palette[1]

        # a pool of light at the base, so the figure stands somewhere instead of floating
        self._add(self._glow(h * 0.30, body_c, 0.10 * light), (cx, base_y))

        # body: a column of light, base to chest, narrowing as it rises.
        # each disc breathes a little more than the one below it. plenty of
        # discs at low brightness, so the column is smooth instead of banded.
        for i in range(14):
            frac = i / 13.0
            r    = h * (0.160 - 0.082 * frac) * width * (1 + 0.020 * breath * frac)
            x    = cx + sway * 2.0 * frac
            y    = base_y - h * (0.12 + 0.50 * frac) - breath * 2.2 * frac
            self._add(self._glow(r, body_c, 0.175 * light), (x, y))

        # shoulders: two soft bumps where the column ends, they rise with the breath.
        # this is what makes the silhouette read as someone instead of something.
        sh_y = base_y - h * 0.645 - breath * 2.6
        for side in (-1, 1):
            self._add(self._glow(h * 0.062, body_c, 0.24 * light),
                      (cx + sway * 2.2 + side * h * 0.085 * width, sh_y))

        # the head: a soft halo with a defined core, bobbing slightly behind the
        # breath, and a faint neck so it never floats free of the shoulders
        tilt   = self.expr["tilt"]
        head_r = h * 0.105
        head_x = cx + sway * 2.6 + tilt * head_r * 0.5
        head_y = base_y - h * 0.785 - math.sin(self.t * math.tau / 4.6 - 0.5) * 2.8
        self._add(self._glow(h * 0.050, body_c, 0.16 * light, spread=1.6),
                  (head_x, sh_y - h * 0.055))
        self._add(self._glow(head_r, body_c, 0.46 * light), (head_x, head_y))
        self._add(self._glow(head_r * 0.78, body_c, 0.30 * light, spread=1.5, focus=1.4),
                  (head_x, head_y))

        # eyes: two warm lights in the face. blink scales them shut, curve lifts
        # them into a smile.
        blink = 1.0
        if self._blink_phase is not None:
            blink = max(0.0, 1.0 - math.sin(math.pi * min(self._blink_phase, 1.0)) * 1.4)
        curve    = self.expr["eye_curve"]
        openness = self.expr["eye_open"] * blink * (1 - curve * 0.35)
        eye_w  = head_r * 0.24 * (1 - curve * 0.25)   # smiles narrow the eyes, not stretch them
        eye_h  = max(eye_w * 0.30, eye_w * 1.1 * openness)
        eye_dx = head_r * 0.50
        eye_y  = head_y + head_r * 0.06 - curve * head_r * 0.12
        warm   = (255, 242, 214)
        for side in (-1, 1):
            ex = head_x + side * eye_dx
            ey = eye_y + side * tilt * head_r * 0.10
            # tight light, so the eyes stay two distinct points instead of one smear
            sprite = self._glow(eye_w, warm, 0.95 * light, spread=1.4, focus=1.0)
            squashed = pygame.transform.scale(
                sprite, (sprite.get_width(), max(2, int(sprite.get_height() * eye_h / eye_w))))
            self._add(squashed, (ex, ey))

        # the symbol: a small light at the chest, pulsing with the breath
        sym_y = base_y - h * 0.50 - breath * 1.8
        self._draw_symbol((cx + sway * 1.5, sym_y), h * 0.040, accent_c,
                          (0.50 + 0.10 * breath) * light)

        # the motes, drifting around the figure
        for m in self.motes:
            mx = cx + math.cos(m["a"]) * m["r"] * 0.85
            my = base_y - h * 0.45 + math.sin(m["a"] * 0.9 + m["phase"]) * m["r"] * 0.55
            twinkle = 0.35 + 0.30 * math.sin(self.t * 2.1 + m["phase"])
            self._add(self._glow(m["size"], accent_c, twinkle * light * 0.6), (mx, my))

        surface.blit(self.canvas,
                     (int(self.pos[0] - cw / 2), int(self.pos[1] - ch + h * 0.08)),
                     special_flags=pygame.BLEND_RGB_ADD)

    def _draw_symbol(self, center, size, color, brightness):
        # the glow behind, then a soft shape on top. the shape stays dim - it is
        # a light inside the figure, not a sticker on it.
        self._add(self._glow(size * 1.6, color, brightness * 0.55), center)
        shape = self.spec.symbol
        x, y  = center
        soft  = tuple(int(c * min(1.0, brightness * 0.55)) for c in color)
        if shape == "star":
            pts = []
            for i in range(10):
                r = size if i % 2 == 0 else size * 0.45
                a = -math.pi / 2 + i * math.pi / 5
                pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
            self._poly(pts, soft)
        elif shape == "spark":
            self._poly([(x, y - size), (x + size * 0.35, y), (x, y + size),
                        (x - size * 0.35, y)], soft)
        elif shape == "lantern":
            self._poly([(x, y - size), (x + size * 0.7, y), (x, y + size),
                        (x - size * 0.7, y)], soft)
            self._add(self._glow(size * 0.40, (255, 240, 200), brightness * 0.8), center)
        else:   # circle, and anything unknown falls back here
            self._add(self._glow(size * 0.6, color, brightness * 0.8), center)

    def _poly(self, points, color):
        temp = pygame.Surface(self.canvas.get_size())
        pygame.draw.polygon(temp, color, [(int(px), int(py)) for px, py in points])
        self.canvas.blit(temp, (0, 0), special_flags=pygame.BLEND_RGB_ADD)


def gentle_guide():
    # the default companion until the builder exists (issue #5)
    return CharacterSpec.from_pack(os.path.join(PACK_DIR, "gentle_guide.json"))


if __name__ == "__main__":
    # meet the character. space cycles expressions, esc leaves.
    pygame.init()
    screen = pygame.display.set_mode((900, 700))
    pygame.display.set_caption("EchoSelf - the character")
    clock  = pygame.time.Clock()
    font   = pygame.font.Font(None, 26)

    sky = pygame.Surface((1, 2))
    sky.set_at((0, 0), (16, 20, 38))
    sky.set_at((0, 1), (52, 44, 80))
    sky = pygame.transform.smoothscale(sky, (900, 700))

    who   = Character(gentle_guide(), pos=(450, 560), height=320)
    names = list(EXPRESSIONS)
    idx   = 0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    idx = (idx + 1) % len(names)
                    who.set_expression(names[idx])
        who.update(dt)
        screen.blit(sky, (0, 0))
        who.draw(screen)
        label = font.render(f"{names[idx]}   (space to change)", True, (220, 220, 220))
        screen.blit(label, (24, 660))
        pygame.display.flip()
    pygame.quit()
