"""procedural character renderer.

a real 2.5d character, drawn entirely by code - no PNGs, no sprite sheets.
the figure is built from layered vector shapes (back hair, robe, arms, head,
face, fringe), every layer drawn fresh each frame at 2x resolution and scaled
down so the edges come out clean. layers move independently - the chest rises
with the breath, the head bobs a beat behind it, the hair follows the head -
which is what makes flat shapes read as someone standing there.

the look is parameters all the way down: skin tone, hair style and color, eye
color, outfit colors, accent palette, form, the chest symbol. they come from a
personality pack's visual block (characters/*.json) or the custom builder.
expressions are parameter targets (eyes, brows, mouth, posture, aura) that the
expression engine drives, the renderer just eases toward whatever is asked.

a soft aura glows behind the figure so they still belong to the EchoSelf sky,
but the character themselves is solid. presence, not a ghost.

preview without the rest of the app:  python -m character.renderer
"""

import os
import json
import math
import random

import pygame

PACK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "characters")

SS = 2   # supersampling factor. draw big, scale down, edges stay smooth

# what the expression engine gets to drive. values are targets, the renderer
# eases toward them so nothing ever snaps.
EXPRESSIONS = {
    "neutral":     dict(eye_open=1.00, eye_curve=0.00, mouth=0.25, brow=0.00,
                        glow=1.00, breath=1.00, sway=1.00, motes=1.00, tilt=0.00),
    "happy":       dict(eye_open=0.65, eye_curve=0.70, mouth=0.90, brow=0.45,
                        glow=1.25, breath=1.10, sway=1.00, motes=1.60, tilt=0.10),
    "patient":     dict(eye_open=0.85, eye_curve=0.25, mouth=0.45, brow=0.25,
                        glow=0.90, breath=0.80, sway=0.70, motes=0.80, tilt=0.18),
    "thinking":    dict(eye_open=0.75, eye_curve=0.00, mouth=0.05, brow=-0.50,
                        glow=0.95, breath=1.00, sway=0.40, motes=0.70, tilt=-0.22),
    "celebrating": dict(eye_open=0.55, eye_curve=0.90, mouth=1.35, brow=0.70,
                        glow=1.50, breath=1.30, sway=1.20, motes=2.40, tilt=0.00),
    "drift":       dict(eye_open=0.55, eye_curve=0.20, mouth=0.30, brow=0.10,
                        glow=0.75, breath=0.65, sway=0.50, motes=0.50, tilt=0.12),
}

FORMS = {"soft": 1.00, "slender": 0.86, "broad": 1.14}   # body width factor


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def shade(color, f):
    # darker (f<1) or lighter (f>1) version of a color
    return tuple(max(0, min(255, int(c * f))) for c in color)


class CharacterSpec:
    # the visual identity. built from a personality pack's visual block, or
    # defaults that look decent on a dark sky.

    def __init__(self, palette=None, glow=0.5, form="soft", symbol="circle",
                 skin="#F2D5C0", hair_style="long", hair_color="#6E5A4E",
                 eye_color="#5B8A80", outfit=None):
        self.palette    = [hex_to_rgb(c) if isinstance(c, str) else tuple(c)
                           for c in (palette or ["#7FB5A8", "#E8DCC8", "#4A6670"])]
        self.glow       = glow
        self.form       = form
        self.symbol     = symbol
        self.skin       = hex_to_rgb(skin) if isinstance(skin, str) else tuple(skin)
        self.hair_style = hair_style
        self.hair_color = hex_to_rgb(hair_color) if isinstance(hair_color, str) else tuple(hair_color)
        self.eye_color  = hex_to_rgb(eye_color) if isinstance(eye_color, str) else tuple(eye_color)
        self.outfit     = [hex_to_rgb(c) if isinstance(c, str) else tuple(c)
                           for c in (outfit or ["#5E8C80", "#4A6E66"])]

    @classmethod
    def from_pack(cls, path):
        # a missing or broken pack should never kill the app, you just get the default figure
        try:
            with open(path, encoding="utf-8") as f:
                v = json.load(f).get("visual", {})
            hair = v.get("hair", {})
            return cls(palette=v.get("palette"),
                       glow=v.get("glow_intensity", 0.5),
                       form=v.get("form", "soft"),
                       symbol=v.get("symbol", "circle"),
                       skin=v.get("skin", "#F2D5C0"),
                       hair_style=hair.get("style", "long"),
                       hair_color=hair.get("color", "#6E5A4E"),
                       eye_color=v.get("eyes", "#5B8A80"),
                       outfit=v.get("outfit"))
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
        self._cache       = {}                         # glow sprites for aura, motes, symbol

        cw, chh     = int(height * 0.95), int(height * 1.08)
        self._cw    = cw
        self._chh   = chh
        self.canvas = pygame.Surface((cw * SS, chh * SS), pygame.SRCALPHA)
        self._aura  = pygame.Surface((cw, chh))        # additive layer behind the figure

        # the motes: little lights that live around the figure
        self.motes = [dict(a=random.uniform(0, math.tau),
                           r=random.uniform(0.34, 0.62) * height,
                           speed=random.uniform(0.08, 0.30) * random.choice((-1, 1)),
                           size=random.randint(2, 4),
                           phase=random.uniform(0, math.tau))
                      for _ in range(12)]

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

    # -- glow (aura, motes, symbol) -------------------------------------------

    def _glow(self, radius, color, brightness, spread=2.0, focus=2.4):
        # a cached radial gradient sprite for the additive light layers
        radius = max(2, int(radius))
        key = (radius, color, round(brightness, 2), spread, focus)
        sprite = self._cache.get(key)
        if sprite is None:
            base = pygame.Surface((48, 48))
            for i in range(24, 0, -1):
                f = ((24 - i) / 24.0) ** focus * brightness
                base_c = (min(255, int(color[0] * f)),
                          min(255, int(color[1] * f)),
                          min(255, int(color[2] * f)))
                pygame.draw.circle(base, base_c, (24, 24), i)
            size   = max(4, int(radius * 2 * spread))
            sprite = pygame.transform.smoothscale(base, (size, size))
            self._cache[key] = sprite
        return sprite

    def _add_to(self, target, sprite, center):
        target.blit(sprite, (int(center[0] - sprite.get_width() / 2),
                             int(center[1] - sprite.get_height() / 2)),
                    special_flags=pygame.BLEND_RGB_ADD)

    # -- geometry helpers (units of h, origin = bottom center, y goes up) -----

    def _pt(self, x, y):
        return (int((self._cw / 2 + x * self.h) * SS),
                int((self._chh - 0.02 * self.h - y * self.h) * SS))

    def _len(self, f):
        return max(1, int(f * self.h * SS))

    def _ellipse(self, color, center, rx, ry, outline=None):
        x, y = self._pt(*center)
        w, hh = self._len(rx), self._len(ry)
        if outline:
            o = max(2, SS * 2)
            pygame.draw.ellipse(self.canvas, outline, (x - w - o, y - hh - o, 2 * (w + o), 2 * (hh + o)))
        pygame.draw.ellipse(self.canvas, color, (x - w, y - hh, 2 * w, 2 * hh))

    def _capsule(self, color, a, b, thickness):
        pa, pb = self._pt(*a), self._pt(*b)
        t = self._len(thickness)
        pygame.draw.line(self.canvas, color, pa, pb, t)
        pygame.draw.circle(self.canvas, color, pa, t // 2)
        pygame.draw.circle(self.canvas, color, pb, t // 2)

    def _polygon(self, color, points, outline=None):
        pts = [self._pt(*p) for p in points]
        if outline:
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            grown = [(int(cx + (px - cx) * 1.035), int(cy + (py - cy) * 1.035)) for px, py in pts]
            pygame.draw.polygon(self.canvas, outline, grown)
        pygame.draw.polygon(self.canvas, color, pts)

    # -- the figure ------------------------------------------------------------

    def draw(self, surface):
        spec    = self.spec
        breath  = math.sin(self.t * math.tau / 4.2)
        sway    = math.sin(self.t * 0.31) * self.expr["sway"]
        width   = FORMS.get(spec.form, 1.0)
        tilt    = self.expr["tilt"]

        # layer offsets, in units of h. this is the 2.5d: the chest rises with
        # the breath, the head lags half a beat behind, the hair follows the head
        body_dy = 0.006 * breath
        head_dx = sway * 0.012 + tilt * 0.018
        head_dy = 0.008 * math.sin(self.t * math.tau / 4.2 - 0.6)

        # -- aura, additive, behind everything --------------------------------
        light = (0.55 + spec.glow * 0.9) * self.expr["glow"]
        accent = spec.palette[0]
        self._aura.fill((0, 0, 0))
        self._add_to(self._aura, self._glow(self.h * 0.34, accent, 0.30 * light),
                     (self._cw / 2, self._chh - 0.50 * self.h))
        self._add_to(self._aura, self._glow(self.h * 0.22, accent, 0.16 * light),
                     (self._cw / 2, self._chh - 0.04 * self.h))
        # the figure's feet land exactly on pos
        top_left = (int(self.pos[0] - self._cw / 2),
                    int(self.pos[1] - self._chh + 0.02 * self.h))
        surface.blit(self._aura, top_left, special_flags=pygame.BLEND_RGB_ADD)

        # -- the solid figure, supersampled ------------------------------------
        self.canvas.fill((0, 0, 0, 0))

        skin     = spec.skin
        hair     = spec.hair_color
        robe     = spec.outfit[0]
        sleeve   = spec.outfit[1] if len(spec.outfit) > 1 else shade(robe, 0.85)
        hair_dk  = shade(hair, 0.62)
        robe_dk  = shade(robe, 0.55)
        skin_dk  = shade(skin, 0.68)

        head_c = (head_dx, 0.76 + head_dy)
        head_r = 0.115

        # back hair, behind everything
        if spec.hair_style != "none":
            self._ellipse(hair, (head_c[0], head_c[1] + 0.01), 0.135, 0.145, outline=hair_dk)
            if spec.hair_style == "long":
                for side in (-1, 1):
                    self._capsule(hair, (head_c[0] + side * 0.115, head_c[1] - 0.02),
                                  (head_c[0] + side * 0.105, 0.50), 0.055)

        # the robe. shoulders, a soft waist, a hem that flares
        sh = 0.145 * width
        self._polygon(robe, [(-sh, 0.60 + body_dy), (sh, 0.60 + body_dy),
                             (0.125 * width, 0.46 + body_dy), (0.115 * width, 0.30),
                             (0.15 * width, 0.02), (-0.15 * width, 0.02),
                             (-0.115 * width, 0.30), (-0.125 * width, 0.46 + body_dy)],
                      outline=robe_dk)
        # shoulder caps, so the silhouette is round where a person is round
        for side in (-1, 1):
            self._ellipse(robe, (side * 0.105 * width, 0.585 + body_dy), 0.048, 0.040)
        # collar, a soft v in the darker tone
        self._polygon(robe_dk, [(-0.052 * width, 0.60 + body_dy), (0.052 * width, 0.60 + body_dy),
                                (0.0, 0.525 + body_dy)])

        # arms: sleeves hanging at the sides, hands showing
        for side in (-1, 1):
            a = (side * 0.125 * width, 0.555 + body_dy)
            b = (side * 0.150 * width + sway * 0.006, 0.315 + body_dy * 0.5)
            self._capsule(sleeve, a, b, 0.054)
            self._ellipse(skin, b, 0.024, 0.024)

        # neck, then the head over it
        self._capsule(skin, (head_dx, 0.66), (head_dx, 0.61 + body_dy), 0.045)
        self._ellipse(skin, head_c, head_r, head_r * 1.06, outline=skin_dk)

        # -- the face -----------------------------------------------------------
        blink = 1.0
        if self._blink_phase is not None:
            blink = max(0.0, 1.0 - math.sin(math.pi * min(self._blink_phase, 1.0)) * 1.4)
        curve    = self.expr["eye_curve"]
        openness = max(0.06, self.expr["eye_open"] * blink * (1 - curve * 0.30))

        eye_y  = head_c[1] - 0.002 + curve * 0.006
        eye_dx = 0.048
        ew, eh = 0.027, 0.024 * openness
        for side in (-1, 1):
            ec = (head_c[0] + side * eye_dx, eye_y + side * tilt * 0.006)
            self._ellipse((250, 248, 240), ec, ew, eh)                     # sclera
            if openness > 0.30:
                self._ellipse(spec.eye_color, ec, 0.014, 0.014 * openness)  # iris
                self._ellipse((30, 28, 34), ec, 0.0065, 0.0065 * openness)  # pupil
                self._ellipse((255, 255, 255),
                              (ec[0] - 0.005, ec[1] + 0.005), 0.0032, 0.0032)  # the spark of life
            else:
                self._capsule(skin_dk, (ec[0] - ew, ec[1]), (ec[0] + ew, ec[1]), 0.006)

        # brows. raised when warm, knit when focused
        brow = self.expr["brow"]
        for side in (-1, 1):
            inner = (head_c[0] + side * 0.022, eye_y + 0.038 + (0.010 if brow < 0 else 0) * brow)
            outer = (head_c[0] + side * 0.070, eye_y + 0.038 + brow * 0.012)
            self._capsule(hair_dk, inner, outer, 0.009)

        # the mouth. flat to smile to open delight
        mouth = self.expr["mouth"]
        mx, my = head_c[0], head_c[1] - 0.062
        if mouth > 1.1:
            self._ellipse((120, 60, 64), (mx, my - 0.008), 0.020, 0.014)   # open smile
            self._ellipse(skin, (mx, my - 0.022), 0.022, 0.010)
        else:
            # corners up, center down. the other way around is a frown.
            pts = []
            for i in range(9):
                a = math.pi * (0.15 + 0.70 * i / 8)
                pts.append(self._pt(mx + math.cos(a) * 0.026,
                                    my + (1 - math.sin(a)) * 0.020 * mouth))
            pygame.draw.lines(self.canvas, skin_dk, False, pts, max(2, SS * 2))

        # a little color in the cheeks when they are happy
        if curve > 0.3:
            blush = pygame.Surface((self._len(0.025) * 2, self._len(0.014) * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(blush, (235, 130, 120, int(70 * curve)), blush.get_rect())
            for side in (-1, 1):
                px, py = self._pt(head_c[0] + side * 0.068, head_c[1] - 0.045)
                self.canvas.blit(blush, (px - blush.get_width() // 2, py - blush.get_height() // 2))

        # front hair, over the face
        if spec.hair_style == "spiky":
            for i in range(7):
                a = math.pi * (0.12 + 0.76 * i / 6)
                tip = (head_c[0] + math.cos(a) * 0.150, head_c[1] + math.sin(a) * 0.155 + 0.01)
                base_l = (head_c[0] + math.cos(a + 0.22) * 0.095, head_c[1] + math.sin(a + 0.22) * 0.095)
                base_r = (head_c[0] + math.cos(a - 0.22) * 0.095, head_c[1] + math.sin(a - 0.22) * 0.095)
                self._polygon(hair, [base_l, tip, base_r])
        elif spec.hair_style != "none":
            # a soft cap high on the head, a fringe parted off-center. the face
            # stays open - hair frames it, never hides it.
            self._ellipse(hair, (head_c[0], head_c[1] + 0.085), 0.116, 0.048, outline=hair_dk)
            self._ellipse(hair, (head_c[0] - 0.062, head_c[1] + 0.066), 0.055, 0.036)
            self._ellipse(hair, (head_c[0] + 0.068, head_c[1] + 0.070), 0.046, 0.032)

        # the chest symbol, a light worn over the heart - painted after the
        # downscale so it can glow over the fabric

        # -- composite ----------------------------------------------------------
        figure = pygame.transform.smoothscale(self.canvas, (self._cw, self._chh))
        surface.blit(figure, top_left)

        # symbol glow on top of the robe
        sym_center = (self.pos[0] + sway * 0.004 * self.h, self.pos[1] - 0.49 * self.h)
        self._draw_symbol(surface, sym_center, self.h * 0.030, spec.palette[1],
                          (0.50 + 0.10 * breath) * light)

        # the motes, drifting around the figure
        for m in self.motes:
            mx = self.pos[0] + math.cos(m["a"]) * m["r"] * 0.85
            my = self.pos[1] - self.h * 0.45 + math.sin(m["a"] * 0.9 + m["phase"]) * m["r"] * 0.5
            twinkle = 0.35 + 0.30 * math.sin(self.t * 2.1 + m["phase"])
            self._add_to(surface, self._glow(m["size"], spec.palette[1], twinkle * light * 0.55),
                         (mx, my))

    def _draw_symbol(self, surface, center, size, color, brightness):
        # a soft light over the heart. glow first, a dim shape inside it.
        self._add_to(surface, self._glow(size * 1.5, color, brightness * 0.45), center)
        shape = self.spec.symbol
        x, y  = center
        soft  = tuple(int(c * min(1.0, brightness * 0.50)) for c in color)
        temp  = pygame.Surface((int(size * 4), int(size * 4)))
        tx = ty = int(size * 2)
        if shape == "star":
            pts = []
            for i in range(10):
                r = size if i % 2 == 0 else size * 0.45
                a = -math.pi / 2 + i * math.pi / 5
                pts.append((tx + math.cos(a) * r, ty + math.sin(a) * r))
            pygame.draw.polygon(temp, soft, pts)
        elif shape in ("spark", "lantern"):
            wf = 0.38 if shape == "spark" else 0.70
            pygame.draw.polygon(temp, soft, [(tx, ty - size), (tx + size * wf, ty),
                                             (tx, ty + size), (tx - size * wf, ty)])
        else:
            pygame.draw.circle(temp, soft, (tx, ty), int(size * 0.6))
        self._add_to(surface, temp, center)
        if shape == "lantern":
            self._add_to(surface, self._glow(size * 0.40, (255, 240, 200), brightness * 0.7), center)


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

    who   = Character(gentle_guide(), pos=(450, 600), height=420)
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
