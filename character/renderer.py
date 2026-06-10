"""procedural character renderer.

a 2.5d character in the style of visual-novel apps - semi-realistic
proportions, a shaped face with a jaw and chin, almond eyes with lashes and
an iris you can fall into, real lips, layered hair with a shine. drawn
entirely by code, no PNGs, no sprite sheets - every shape is a polygon or a
curve computed each frame at 2x resolution and scaled down so the lines come
out clean.

the layering is the 2.5d: back hair, body, face, front hair are separate
passes with separate motion - the chest rises with the breath, the head lags
half a beat behind, the hair follows the head. translucent shading (the jaw
shadow, the hair shine, the skirt folds) is blitted, never drawn, so it
blends instead of punching holes in the alpha.

the look is parameters all the way down: skin tone, hair style and color,
eye color, outfit colors, accent palette, form, the chest symbol - from a
personality pack's visual block (characters/*.json) or the custom builder.
expressions are parameter targets the expression engine drives.

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
    "happy":       dict(eye_open=0.70, eye_curve=0.70, mouth=0.90, brow=0.45,
                        glow=1.25, breath=1.10, sway=1.00, motes=1.60, tilt=0.10),
    "patient":     dict(eye_open=0.85, eye_curve=0.25, mouth=0.45, brow=0.25,
                        glow=0.90, breath=0.80, sway=0.70, motes=0.80, tilt=0.18),
    "thinking":    dict(eye_open=0.78, eye_curve=0.00, mouth=0.05, brow=-0.50,
                        glow=0.95, breath=1.00, sway=0.40, motes=0.70, tilt=-0.22),
    "celebrating": dict(eye_open=0.60, eye_curve=0.90, mouth=1.35, brow=0.70,
                        glow=1.50, breath=1.30, sway=1.20, motes=2.40, tilt=0.00),
    "drift":       dict(eye_open=0.55, eye_curve=0.20, mouth=0.30, brow=0.10,
                        glow=0.75, breath=0.65, sway=0.50, motes=0.50, tilt=0.12),
}

FORMS = {"soft": 1.00, "slender": 0.90, "broad": 1.12}   # body width factor


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def shade(color, f):
    # darker (f<1) or lighter (f>1) version of a color
    return tuple(max(0, min(255, int(c * f))) for c in color)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def bezier(p0, p1, p2, n=14):
    # quadratic bezier, sampled. enough for every curve in the figure.
    pts = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        pts.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return pts


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
    def from_visual(cls, v):
        # build a spec from a pack's visual block (a dict)
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

    @classmethod
    def from_pack(cls, path):
        # a missing or broken pack should never kill the app, you just get the default figure
        try:
            with open(path, encoding="utf-8") as f:
                return cls.from_visual(json.load(f).get("visual", {}))
        except (OSError, ValueError):
            return cls()


class Character:
    # the figure itself. update(dt) moves the breath, the blink, the motes,
    # draw(surface) paints it. pos is where the figure's feet land.

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

        cw, chh     = int(height * 0.72), int(height * 1.04)
        self._cw    = cw
        self._chh   = chh
        self.canvas = pygame.Surface((cw * SS, chh * SS), pygame.SRCALPHA)
        self._aura  = pygame.Surface((cw, chh))        # additive layer behind the figure

        # the motes: little lights that live around the figure
        self.motes = [dict(a=random.uniform(0, math.tau),
                           r=random.uniform(0.30, 0.55) * height,
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
                int((self._chh - 0.015 * self.h - y * self.h) * SS))

    def _len(self, f):
        return max(1, int(f * self.h * SS))

    def _poly(self, color, pts_units):
        pygame.draw.polygon(self.canvas, color, [self._pt(*p) for p in pts_units])

    def _ell(self, color, center, rx, ry):
        x, y = self._pt(*center)
        w, h = self._len(rx), self._len(ry)
        pygame.draw.ellipse(self.canvas, color, (x - w, y - h, 2 * w, 2 * h))

    def _strip(self, color, path_units, w_from, w_to):
        # a tapered ribbon along a path - arms, brows, strands
        path = [self._pt(*p) for p in path_units]
        left, right = [], []
        n = len(path)
        for i, (x, y) in enumerate(path):
            t  = i / (n - 1)
            w  = (w_from + (w_to - w_from) * t) * self.h * SS / 2
            if i < n - 1:
                dx, dy = path[i + 1][0] - x, path[i + 1][1] - y
            else:
                dx, dy = x - path[i - 1][0], y - path[i - 1][1]
            d = math.hypot(dx, dy) or 1
            nx, ny = -dy / d, dx / d
            left.append((x + nx * w, y + ny * w))
            right.append((x - nx * w, y - ny * w))
        pygame.draw.polygon(self.canvas, color, left + right[::-1])

    def _tell(self, rgba, center, rx, ry):
        # translucent ellipse, blitted so it blends instead of replacing alpha
        w, h = self._len(rx), self._len(ry)
        temp = pygame.Surface((2 * w, 2 * h), pygame.SRCALPHA)
        pygame.draw.ellipse(temp, rgba, temp.get_rect())
        x, y = self._pt(*center)
        self.canvas.blit(temp, (x - w, y - h))

    # -- the figure ------------------------------------------------------------

    def draw(self, surface):
        spec    = self.spec
        breath  = math.sin(self.t * math.tau / 4.2)
        sway    = math.sin(self.t * 0.31) * self.expr["sway"]
        W       = FORMS.get(spec.form, 1.0)
        tilt    = self.expr["tilt"]

        body_dy = 0.005 * breath                                  # the chest rises
        hx      = sway * 0.010 + tilt * 0.012                     # the head lags and leans
        hy      = 0.906 + 0.006 * math.sin(self.t * math.tau / 4.2 - 0.6)

        # -- aura, additive, behind everything --------------------------------
        light  = (0.55 + spec.glow * 0.9) * self.expr["glow"]
        accent = spec.palette[0]
        self._aura.fill((0, 0, 0))
        self._add_to(self._aura, self._glow(self.h * 0.30, accent, 0.26 * light),
                     (self._cw / 2, self._chh - 0.55 * self.h))
        self._add_to(self._aura, self._glow(self.h * 0.20, accent, 0.14 * light),
                     (self._cw / 2, self._chh - 0.04 * self.h))
        top_left = (int(self.pos[0] - self._cw / 2),
                    int(self.pos[1] - self._chh + 0.015 * self.h))
        surface.blit(self._aura, top_left, special_flags=pygame.BLEND_RGB_ADD)

        # -- palette ------------------------------------------------------------
        skin    = spec.skin
        skin_dk = shade(skin, 0.78)
        hair    = spec.hair_color
        hair_dk = shade(hair, 0.66)
        hair_lt = shade(hair, 1.30)
        top_c   = spec.outfit[0]
        skirt_c = spec.outfit[1] if len(spec.outfit) > 1 else shade(top_c, 0.88)
        lip     = mix(skin, (186, 92, 96), 0.62)

        self.canvas.fill((0, 0, 0, 0))

        # -- back hair -----------------------------------------------------------
        if spec.hair_style != "none":
            self._back_hair(hx, hy, hair, hair_dk)

        # -- the body ------------------------------------------------------------
        sh_y, sh_w = 0.812 + body_dy, 0.080 * W
        wa_y, wa_w = 0.630 + body_dy * 0.5, 0.054 * W
        hp_w       = 0.080 * W
        hem_w      = 0.108 * W

        # skirt: waist through hips, flaring to the hem, swaying a little
        right = bezier((wa_w, wa_y), (hp_w + 0.012, 0.50), (hem_w + sway * 0.006, 0.022))
        left  = bezier((-wa_w, wa_y), (-hp_w - 0.012, 0.50), (-hem_w + sway * 0.006, 0.022))
        self._poly(skirt_c, right + [(right[-1][0], 0.018), (left[-1][0], 0.018)] + left[::-1])
        # fold shadows down the skirt
        for fx in (-0.45, 0.05, 0.5):
            x0 = wa_w * fx
            x1 = hem_w * fx * 1.1
            self._strip((*shade(skirt_c, 0.84), 110),
                        bezier((x0, wa_y - 0.02), ((x0 + x1) / 2, 0.36), (x1, 0.04)),
                        0.004, 0.014)

        # bodice: fitted, shoulders to waist
        r = bezier((sh_w, sh_y), (sh_w + 0.006, 0.72), (wa_w, wa_y))
        l = bezier((-sh_w, sh_y), (-sh_w - 0.006, 0.72), (-wa_w, wa_y))
        self._poly(top_c, r + l[::-1])
        # neckline
        self._poly(skin, [(-0.023 * W, sh_y + 0.004), (0.023 * W, sh_y + 0.004), (0, 0.764 + body_dy)])
        self._poly(shade(top_c, 0.8), [(-0.032 * W, sh_y + 0.006), (-0.024 * W, sh_y + 0.006),
                                       (0, 0.762 + body_dy), (-0.004, 0.755 + body_dy)])
        self._poly(shade(top_c, 0.8), [(0.032 * W, sh_y + 0.006), (0.024 * W, sh_y + 0.006),
                                       (0.004, 0.755 + body_dy), (0, 0.762 + body_dy)])
        # side shading on the bodice, hugging the edge
        self._tell((*shade(top_c, 0.72), 44), (sh_w * 0.80, 0.715), 0.011, 0.080)

        # arms: shoulder, a soft elbow, the hand. sleeves in the top's color.
        for s in (-1, 1):
            path = bezier((s * 0.072 * W, 0.800 + body_dy),
                          (s * 0.094 * W, 0.650),
                          (s * 0.082 * W + sway * 0.004, 0.487))
            self._strip(top_c, path, 0.034, 0.020)
            self._ell(skin, path[-1], 0.0125, 0.016)

        # neck, then the face
        self._poly(skin, [(-0.0185 + hx * 0.6, 0.822), (0.0185 + hx * 0.6, 0.822),
                          (0.0165 + hx, hy - 0.052), (-0.0165 + hx, hy - 0.052)])
        self._tell((*skin_dk, 50), (hx * 0.85, hy - 0.0585), 0.013, 0.006)   # under-jaw shadow

        self._face(hx, hy, skin, skin_dk, lip)

        # -- front hair ------------------------------------------------------------
        if spec.hair_style != "none":
            self._front_hair(hx, hy, hair, hair_dk, hair_lt)

        # -- composite ----------------------------------------------------------
        figure = pygame.transform.smoothscale(self.canvas, (self._cw, self._chh))
        surface.blit(figure, top_left)

        # symbol at the chest, over the fabric
        sym = (self.pos[0] + sway * 0.004 * self.h, self.pos[1] - 0.70 * self.h)
        self._draw_symbol(surface, sym, self.h * 0.024, spec.palette[1],
                          (0.50 + 0.10 * breath) * light)

        # the motes, drifting around the figure
        for m in self.motes:
            mx = self.pos[0] + math.cos(m["a"]) * m["r"] * 0.85
            my = self.pos[1] - self.h * 0.52 + math.sin(m["a"] * 0.9 + m["phase"]) * m["r"] * 0.5
            twinkle = 0.35 + 0.30 * math.sin(self.t * 2.1 + m["phase"])
            self._add_to(surface, self._glow(m["size"], spec.palette[1], twinkle * light * 0.5),
                         (mx, my))

    # -- the face ---------------------------------------------------------------

    def _face(self, hx, hy, skin, skin_dk, lip):
        rx, chin = 0.0525, hy - 0.0700

        # the face shape: a skull arc over a tapered jaw down to the chin
        pts = []
        for i in range(15):
            a = math.pi * i / 14
            pts.append((hx + math.cos(a) * rx, hy + 0.010 + math.sin(a) * 0.058))
        pts = [(hx + rx, hy + 0.010)] + pts[::-1]  # right -> over the top -> left
        jaw_l = bezier((hx - rx, hy + 0.008), (hx - rx + 0.006, hy - 0.046), (hx - 0.011, chin))
        jaw_r = bezier((hx + 0.011, chin), (hx + rx - 0.006, hy - 0.046), (hx + rx, hy + 0.008))
        self._poly(skin, pts[1:] + jaw_l + [(hx, chin - 0.0015)] + jaw_r)
        # one soft shadow along the right of the face, for depth
        self._tell((*skin_dk, 46), (hx + rx * 0.62, hy - 0.018), 0.016, 0.042)

        curve    = self.expr["eye_curve"]
        blink = 1.0
        if self._blink_phase is not None:
            blink = max(0.0, 1.0 - math.sin(math.pi * min(self._blink_phase, 1.0)) * 1.4)
        openness = max(0.0, self.expr["eye_open"] * blink * (1 - curve * 0.28))

        ey = hy - 0.007 + curve * 0.004
        for s in (-1, 1):
            self._eye((hx + s * 0.0245, ey + s * self.expr["tilt"] * 0.004), s, openness, curve)

        # brows: thin, tapered, raised when warm, knit when focused
        brow = self.expr["brow"]
        for s in (-1, 1):
            inner = (hx + s * 0.0110, ey + 0.0300 + (0.008 * brow if brow < 0 else 0))
            mid   = (hx + s * 0.0260, ey + 0.0345 + brow * 0.009)
            outer = (hx + s * 0.0390, ey + 0.0305 + brow * 0.012)
            self._strip(shade(self.spec.hair_color, 0.55), [inner, mid, outer], 0.0036, 0.0012)

        # the nose: one short line of shadow, nothing more
        self._strip((*skin_dk, 150), [(hx + 0.0025, hy - 0.0195), (hx + 0.0045, hy - 0.0290),
                                      (hx - 0.0015, hy - 0.0310)], 0.0022, 0.0028)

        # lips: a darker upper, a fuller lower with a little light on it
        mouth = self.expr["mouth"]
        my    = hy - 0.0468
        mw    = 0.0200
        lift  = min(mouth, 1.0) * 0.0050
        if mouth > 1.1:   # open delight
            self._ell(shade(lip, 0.52), (hx, my - 0.003), 0.0125, 0.0085)
            self._ell((252, 250, 246), (hx, my + 0.0012), 0.0085, 0.0028)
        else:
            top = bezier((hx - mw, my + lift), (hx, my - 0.0014 + mouth * 0.001), (hx + mw, my + lift))
            self._strip(shade(lip, 0.82), top, 0.0026, 0.0026)
            bot = bezier((hx - mw * 0.80, my + lift - 0.0010), (hx, my - 0.0054 + lift * 0.4),
                         (hx + mw * 0.80, my + lift - 0.0010))
            self._strip(lip, bot, 0.0030, 0.0030)
            self._tell((255, 240, 238, 46), (hx, my - 0.0040 + lift * 0.4), 0.0042, 0.0011)

        # a little color in the cheeks when they are happy
        if curve > 0.3:
            for s in (-1, 1):
                self._tell((232, 128, 122, int(60 * curve)), (hx + s * 0.034, hy - 0.026),
                           0.0125, 0.0070)

    def _eye(self, center, side, openness, curve):
        # built on its own little surface and clipped to the almond, so the
        # iris can be big without spilling onto the face
        ex, ey = center
        hw     = 0.0195
        top_h  = 0.0130 * max(openness, 0.05) + curve * 0.0015
        bot_h  = 0.0085 * (0.55 + 0.45 * openness)

        cx, cy = self._pt(ex, ey)
        w_px   = self._len(hw * 2.4)
        h_px   = self._len(0.06)
        ox, oy = cx - w_px // 2, cy - h_px // 2

        def local(pts):
            return [(self._pt(*p)[0] - ox, self._pt(*p)[1] - oy) for p in pts]

        lid_top = bezier((ex - hw, ey), (ex + side * 0.002, ey + top_h * 2), (ex + hw, ey + 0.001))
        lid_bot = bezier((ex + hw, ey + 0.001), (ex, ey - bot_h * 2), (ex - hw, ey))
        almond  = local(lid_top + lid_bot)

        if openness < 0.16:
            # closed: just the lash line, soft
            self._strip((44, 32, 34), lid_top, 0.0030, 0.0030)
            return

        eye  = pygame.Surface((w_px, h_px), pygame.SRCALPHA)
        mask = pygame.Surface((w_px, h_px), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), almond)
        pygame.draw.polygon(eye, (250, 247, 242), almond)

        # iris, pupil, the lights in it
        ic     = self.spec.eye_color
        ir     = self._len(0.0105)
        icx    = local([(ex, ey + 0.001)])[0]
        pygame.draw.circle(eye, shade(ic, 0.55), icx, ir)
        pygame.draw.circle(eye, ic, icx, int(ir * 0.82))
        pygame.draw.circle(eye, shade(ic, 1.35), (icx[0], icx[1] + int(ir * 0.3)), int(ir * 0.45))
        pygame.draw.circle(eye, (28, 24, 28), icx, int(ir * 0.42))
        pygame.draw.circle(eye, (255, 255, 255), (icx[0] - int(ir * 0.35), icx[1] - int(ir * 0.35)),
                           int(ir * 0.26))
        pygame.draw.circle(eye, (255, 255, 255, 180), (icx[0] + int(ir * 0.40), icx[1] + int(ir * 0.42)),
                           int(ir * 0.12))

        eye.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.canvas.blit(eye, (ox, oy))

        # the lash line, heavier toward the outer corner, with a small wing
        self._strip((40, 30, 32), lid_top, 0.0026, 0.0042)
        wing_x = ex + side * hw
        self._strip((40, 30, 32), [(wing_x, ey + 0.001), (wing_x + side * 0.0035, ey + 0.0035)],
                    0.0030, 0.0008)

    # -- hair ---------------------------------------------------------------------

    def _back_hair(self, hx, hy, hair, hair_dk):
        style = self.spec.hair_style
        if style == "long":
            crown = hy + 0.075
            r = bezier((hx, crown), (hx + 0.085, hy + 0.020), (hx + 0.080, 0.74))
            r += bezier((hx + 0.080, 0.74), (hx + 0.072, 0.62), (hx + 0.048, 0.555))
            l = bezier((hx, crown), (hx - 0.085, hy + 0.020), (hx - 0.080, 0.74))
            l += bezier((hx - 0.080, 0.74), (hx - 0.072, 0.62), (hx - 0.048, 0.555))
            self._poly(hair_dk, r + [(hx + 0.020, 0.545), (hx - 0.020, 0.545)] + l[::-1])
            self._ell(hair, (hx, hy + 0.020), 0.064, 0.066)
        elif style == "short":
            self._ell(hair_dk, (hx, hy + 0.004), 0.066, 0.072)
            self._ell(hair, (hx, hy + 0.016), 0.061, 0.062)
        elif style == "spiky":
            for i in range(7):
                a   = math.pi * (0.10 + 0.80 * i / 6)
                tip = (hx + math.cos(a) * 0.085, hy + 0.012 + math.sin(a) * 0.088)
                bl  = (hx + math.cos(a + 0.30) * 0.048, hy + 0.012 + math.sin(a + 0.30) * 0.050)
                br  = (hx + math.cos(a - 0.30) * 0.048, hy + 0.012 + math.sin(a - 0.30) * 0.050)
                self._poly(hair_dk, [bl, tip, br])
            self._ell(hair, (hx, hy + 0.012), 0.056, 0.058)

    def _front_hair(self, hx, hy, hair, hair_dk, hair_lt):
        style = self.spec.hair_style
        rx    = 0.0525
        if style == "spiky":
            for i in range(6):
                a   = math.pi * (0.22 + 0.56 * i / 5)
                tip = (hx + math.cos(a) * 0.066, hy + 0.018 + math.sin(a) * 0.068)
                bl  = (hx + math.cos(a + 0.24) * 0.038, hy + 0.022 + math.sin(a + 0.24) * 0.040)
                br  = (hx + math.cos(a - 0.24) * 0.038, hy + 0.022 + math.sin(a - 0.24) * 0.040)
                self._poly(hair, [bl, tip, br])
            self._tell((*hair_lt, 70), (hx - 0.012, hy + 0.052), 0.030, 0.012)
            return

        # a fringe swept across the forehead from an off-center part
        part = (hx - 0.014, hy + 0.064)
        sweep = bezier(part, (hx + 0.035, hy + 0.052), (hx + 0.0505, hy + 0.010))
        hairline = bezier((hx + 0.0505, hy + 0.010), (hx + 0.010, hy + 0.030), (hx - 0.0505, hy + 0.014))
        crown = bezier((hx - 0.0505, hy + 0.014), (hx - 0.058, hy + 0.052), (part[0], part[1]))
        self._poly(hair, sweep + hairline + crown)
        # a quiet shine across the crown, kept inside the hair
        self._tell((*hair_lt, 50), (hx - 0.008, hy + 0.056), 0.024, 0.0075)

        # strands framing the face
        for s, ln in ((-1, 0.66), (1, 0.67)):
            p = bezier((hx + s * rx * 0.96, hy + 0.018),
                       (hx + s * (rx + 0.013), hy - 0.052),
                       (hx + s * (rx + 0.004), ln))
            self._strip(hair, p, 0.0175, 0.0070)
        if style == "long":
            # and the long fall over the shoulders, curving out then in
            for s in (-1, 1):
                p = bezier((hx + s * rx * 0.9, hy - 0.022),
                           (hx + s * 0.088, 0.70),
                           (hx + s * 0.052, 0.585))
                self._strip(hair, p, 0.0190, 0.0100)

    # -- symbol -------------------------------------------------------------------

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
    # the default companion until session zero has happened
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

    who   = Character(gentle_guide(), pos=(450, 660), height=600)
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
