"""procedural 2.5D character, drawn entirely by code - the fallback when no art pack is set."""

import os
import json
import math
import random

import pygame

from core import paths

PACK_DIR = os.path.join(paths.resource_root(), "characters")

SS = 3   # supersampling factor. draw big, scale down, edges stay smooth and soft

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
                 eye_color="#5B8A80", outfit=None, gender="female", art=None):
        self.art        = art       # an art-pack id under characters/art/, or None
        self.palette    = [hex_to_rgb(c) if isinstance(c, str) else tuple(c)
                           for c in (palette or ["#7FB5A8", "#E8DCC8", "#4A6670"])]
        self.glow       = glow
        self.form       = form
        self.symbol     = symbol
        self.gender     = gender
        self.skin       = hex_to_rgb(skin) if isinstance(skin, str) else tuple(skin)
        self.hair_style = hair_style
        self.hair_color = hex_to_rgb(hair_color) if isinstance(hair_color, str) else tuple(hair_color)
        self.eye_color  = hex_to_rgb(eye_color) if isinstance(eye_color, str) else tuple(eye_color)
        self.outfit     = [hex_to_rgb(c) if isinstance(c, str) else tuple(c)
                           for c in (outfit or ["#5E8C80", "#4A6E66"])]

    @classmethod
    def from_visual(cls, v):
        hair = v.get("hair", {})
        return cls(palette=v.get("palette"),
                   glow=v.get("glow_intensity", 0.5),
                   form=v.get("form", "soft"),
                   symbol=v.get("symbol", "circle"),
                   gender=v.get("gender", "female"),
                   skin=v.get("skin", "#F2D5C0"),
                   hair_style=hair.get("style", "long"),
                   hair_color=hair.get("color", "#6E5A4E"),
                   eye_color=v.get("eyes", "#5B8A80"),
                   outfit=v.get("outfit"),
                   art=v.get("art"))

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
        self._blink_phase = None
        self._next_blink  = random.uniform(2.0, 5.0)
        self._cache       = {}

        cw, chh     = int(height * 0.74), int(height * 1.05)
        self._cw    = cw
        self._chh   = chh
        self.canvas = pygame.Surface((cw * SS, chh * SS), pygame.SRCALPHA)
        self._aura  = pygame.Surface((cw, chh))

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

        k = 1.0 - math.exp(-4.0 * dt)
        for key in self.expr:
            self.expr[key] += (self.target[key] - self.expr[key]) * k

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
        # a tapered ribbon along a path - hair strands, arms, brows, lips
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
        male    = spec.gender == "male"
        breath  = math.sin(self.t * math.tau / 4.2)
        sway    = math.sin(self.t * 0.31) * self.expr["sway"]
        W       = FORMS.get(spec.form, 1.0) * (1.12 if male else 1.0)
        tilt    = self.expr["tilt"]

        body_dy = 0.005 * breath
        hx      = sway * 0.010 + tilt * 0.012
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
        skin_dk = shade(skin, 0.80)
        hair    = spec.hair_color
        hair_dk = shade(hair, 0.68)
        hair_lt = shade(hair, 1.32)
        top_c   = spec.outfit[0]
        low_c   = spec.outfit[1] if len(spec.outfit) > 1 else shade(top_c, 0.88)
        lip     = mix(skin, (186, 92, 96), 0.30 if male else 0.62)

        self.canvas.fill((0, 0, 0, 0))

        if spec.hair_style != "none":
            self._back_hair(hx, hy, hair, hair_dk, male)

        # -- the body ------------------------------------------------------------
        sh_w = (0.082 if male else 0.070) * W   # narrower shoulders = the head reads bigger
        sh_y = 0.812 + body_dy
        wa_w = (0.062 if male else 0.054) * W
        wa_y = 0.630 + body_dy * 0.5

        if male:
            # straight trousers, the lightest hint of a taper, a center seam
            hem_w = 0.058 * W
            self._poly(low_c, [(-wa_w, wa_y), (wa_w, wa_y),
                               (hem_w + sway * 0.004, 0.022), (-hem_w + sway * 0.004, 0.022)])
            self._strip((*shade(low_c, 0.78), 130),
                        [(sway * 0.002, wa_y - 0.04), (sway * 0.004, 0.04)], 0.004, 0.006)
            # a long shirt, shoulders to below the waist, a belt line
            r = bezier((sh_w, sh_y), (sh_w + 0.002, 0.70), (wa_w + 0.006, wa_y - 0.012))
            l = bezier((-sh_w, sh_y), (-sh_w - 0.002, 0.70), (-wa_w - 0.006, wa_y - 0.012))
            self._poly(top_c, r + l[::-1])
            self._strip(shade(top_c, 0.66), [(-wa_w - 0.004, wa_y - 0.008),
                                             (wa_w + 0.004, wa_y - 0.008)], 0.007, 0.007)
            # collar: a small open v
            self._poly(skin, [(-0.020 * W, sh_y + 0.004), (0.020 * W, sh_y + 0.004),
                              (0, 0.778 + body_dy)])
            for s in (-1, 1):
                self._poly(shade(top_c, 0.8), [(s * 0.024 * W, sh_y + 0.006),
                                               (s * 0.014 * W, sh_y + 0.004),
                                               (s * 0.002, 0.772 + body_dy),
                                               (s * 0.006, 0.778 + body_dy)])
        else:
            # skirt: waist through hips, flaring to the hem, swaying a little
            hp_w, hem_w = 0.080 * W, 0.108 * W
            right = bezier((wa_w, wa_y), (hp_w + 0.012, 0.50), (hem_w + sway * 0.006, 0.022))
            left  = bezier((-wa_w, wa_y), (-hp_w - 0.012, 0.50), (-hem_w + sway * 0.006, 0.022))
            self._poly(low_c, right + [(right[-1][0], 0.018), (left[-1][0], 0.018)] + left[::-1])
            for fx in (-0.45, 0.05, 0.5):
                self._strip((*shade(low_c, 0.84), 110),
                            bezier((wa_w * fx, wa_y - 0.02), ((wa_w * fx + hem_w * fx * 1.1) / 2, 0.36),
                                   (hem_w * fx * 1.1, 0.04)),
                            0.004, 0.014)
            # fitted bodice
            r = bezier((sh_w, sh_y), (sh_w + 0.006, 0.72), (wa_w, wa_y))
            l = bezier((-sh_w, sh_y), (-sh_w - 0.006, 0.72), (-wa_w, wa_y))
            self._poly(top_c, r + l[::-1])
            self._poly(skin, [(-0.023 * W, sh_y + 0.004), (0.023 * W, sh_y + 0.004),
                              (0, 0.764 + body_dy)])
            for s in (-1, 1):
                self._poly(shade(top_c, 0.8), [(s * 0.032 * W, sh_y + 0.006),
                                               (s * 0.024 * W, sh_y + 0.006),
                                               (s * 0.004, 0.755 + body_dy),
                                               (s * 0.000, 0.762 + body_dy)])
        # side shading, hugging the edge
        self._tell((*shade(top_c, 0.72), 44), (sh_w * 0.80, 0.715), 0.011, 0.080)

        # arms: shoulder, a soft elbow, the hand
        arm_w = 0.040 if male else 0.034
        for s in (-1, 1):
            path = bezier((s * (sh_w - 0.008), 0.800 + body_dy),
                          (s * (sh_w + 0.014), 0.650),
                          (s * (sh_w + 0.002) + sway * 0.004, 0.498))
            self._strip(top_c, path, arm_w, arm_w * 0.6)
            self._ell(skin, path[-1], 0.0105, 0.0135)

        # neck, then the face
        nk = 0.0225 if male else 0.0185
        self._poly(skin, [(-nk + hx * 0.6, 0.822), (nk + hx * 0.6, 0.822),
                          (nk * 0.9 + hx, hy - 0.052), (-nk * 0.9 + hx, hy - 0.052)])
        self._tell((*skin_dk, 50), (hx * 0.85, hy - 0.0585), 0.013, 0.006)

        self._face(hx, hy, skin, skin_dk, lip, male)

        if spec.hair_style != "none":
            self._front_hair(hx, hy, hair, hair_dk, hair_lt, male)

        # -- composite ----------------------------------------------------------
        # a touch of soft focus: scale down a little then back up, so the features
        # read gentle instead of stark - less "cut from paper", more painted.
        figure = pygame.transform.smoothscale(self.canvas, (self._cw, self._chh))
        soft   = pygame.transform.smoothscale(figure, (int(self._cw * 0.82), int(self._chh * 0.82)))
        figure = pygame.transform.smoothscale(soft, (self._cw, self._chh))
        surface.blit(figure, top_left)

        sym = (self.pos[0] + sway * 0.004 * self.h, self.pos[1] - 0.70 * self.h)
        self._draw_symbol(surface, sym, self.h * 0.024, spec.palette[1],
                          (0.50 + 0.10 * breath) * light)

        for m in self.motes:
            mx = self.pos[0] + math.cos(m["a"]) * m["r"] * 0.85
            my = self.pos[1] - self.h * 0.52 + math.sin(m["a"] * 0.9 + m["phase"]) * m["r"] * 0.5
            twinkle = 0.35 + 0.30 * math.sin(self.t * 2.1 + m["phase"])
            self._add_to(surface, self._glow(m["size"], spec.palette[1], twinkle * light * 0.5),
                         (mx, my))

    # -- the face ---------------------------------------------------------------
    # the proportions that make it read like the reference art and not like a
    # mannequin: a short round face with a small chin, eyes nearly twice the
    # "realistic" size sitting at the face's center, lashes only on top, brows
    # thin and high. measured against the art, not against anatomy.

    def _face(self, hx, hy, skin, skin_dk, lip, male):
        rx   = 0.0590 if male else 0.0575     # wide at the cheekbones
        chin = hy - (0.0640 if male else 0.0615)   # and short to the chin
        c_w  = 0.0170 if male else 0.0085

        # one continuous loop: over the skull, down the left jaw, across the
        # chin, up the right jaw. anything self-crossing makes pygame's
        # scanline fill bleed a seam straight through the eyes.
        arc = []
        for i in range(15):
            a = math.pi * i / 14
            arc.append((hx + math.cos(a) * rx, hy + 0.012 + math.sin(a) * 0.056))
        jaw_l = bezier((hx - rx, hy + 0.010), (hx - rx + 0.004, hy - 0.038), (hx - c_w, chin))
        jaw_r = bezier((hx + c_w, chin), (hx + rx - 0.004, hy - 0.038), (hx + rx, hy + 0.010))
        self._poly(skin, arc + jaw_l + [(hx, chin - 0.0012)] + jaw_r)
        self._tell((*skin_dk, 36), (hx + rx * 0.66, hy - 0.014), 0.014, 0.038)

        curve = self.expr["eye_curve"]
        blink = 1.0
        if self._blink_phase is not None:
            blink = max(0.0, 1.0 - math.sin(math.pi * min(self._blink_phase, 1.0)) * 1.4)
        openness = max(0.0, self.expr["eye_open"] * blink * (1 - curve * 0.28))

        ey = hy - 0.0105 + curve * 0.004
        for s in (-1, 1):
            self._eye((hx + s * 0.0290, ey + s * self.expr["tilt"] * 0.004), s,
                      openness, curve, male)

        # brows: thin, high, a soft arch. expression moves them, never anger
        # by default.
        brow = self.expr["brow"]
        b_y  = 0.0335 if male else 0.0365
        b_w  = (0.0042, 0.0014) if male else (0.0026, 0.0010)
        arch = 0.0026 if male else 0.0040
        for s in (-1, 1):
            inner = (hx + s * 0.0130, ey + b_y + (0.008 * brow if brow < 0 else 0))
            mid   = (hx + s * 0.0290, ey + b_y + arch + brow * 0.009)
            outer = (hx + s * 0.0435, ey + b_y + 0.0002 + brow * 0.012)
            self._strip(shade(self.spec.hair_color, 0.60), [inner, mid, outer], b_w[0], b_w[1])

        # the nose: barely there. a small soft stroke, not a mark.
        self._strip((*skin_dk, 85), [(hx + 0.0022, hy - 0.0300), (hx - 0.0008, hy - 0.0345)],
                    0.0018, 0.0024)

        # the mouth: small and soft, sitting low on the short face
        mouth = self.expr["mouth"]
        my    = hy - 0.0455
        mw    = 0.0130
        lift  = min(mouth, 1.0) * 0.0042
        if mouth > 1.1:
            self._ell(shade(lip, 0.55), (hx, my - 0.0025), 0.0100, 0.0070)
            self._ell((252, 250, 246), (hx, my + 0.0010), 0.0068, 0.0022)
        elif male:
            line = bezier((hx - mw, my + lift), (hx, my - 0.0010 + mouth * 0.001),
                          (hx + mw, my + lift))
            self._strip(shade(lip, 0.72), line, 0.0024, 0.0024)
        else:
            top = bezier((hx - mw, my + lift), (hx, my - 0.0012 + mouth * 0.001),
                         (hx + mw, my + lift))
            self._strip(shade(lip, 0.85), top, 0.0024, 0.0024)
            bot = bezier((hx - mw * 0.72, my + lift - 0.0008), (hx, my - 0.0048 + lift * 0.4),
                         (hx + mw * 0.72, my + lift - 0.0008))
            self._strip(lip, bot, 0.0028, 0.0028)
            self._tell((255, 240, 238, 50), (hx, my - 0.0036 + lift * 0.4), 0.0036, 0.0010)

        # color in the cheeks, just under the eyes like the reference. hers is
        # always faintly there, his only shows when genuinely delighted.
        blush_a = int((30 if not male else 0) + 55 * max(0.0, curve - 0.1))
        if blush_a > 0:
            for s in (-1, 1):
                self._tell((236, 140, 130, blush_a), (hx + s * 0.040, hy - 0.0285),
                           0.0130, 0.0062)

    def _eye(self, center, side, openness, curve, male):
        # nearly twice "realistic" size - this is where the style lives. a big
        # iris under a heavy top lash, no outline anywhere else, light inside.
        ex, ey = center
        hw     = 0.0245 if male else 0.0265
        top_h  = (0.0165 if male else 0.0205) * max(openness, 0.05) + curve * 0.0015
        bot_h  = 0.0105 * (0.55 + 0.45 * openness)

        cx, cy = self._pt(ex, ey)
        w_px   = self._len(hw * 2.6)
        h_px   = self._len(0.095)
        ox, oy = cx - w_px // 2, cy - h_px // 2

        def local(pts):
            return [(self._pt(*p)[0] - ox, self._pt(*p)[1] - oy) for p in pts]

        lid_top = bezier((ex - hw, ey + 0.002 * side), (ex + side * 0.002, ey + top_h * 2),
                         (ex + hw, ey + 0.003))
        lid_bot = bezier((ex + hw, ey + 0.003), (ex, ey - bot_h * 2), (ex - hw, ey + 0.002 * side))
        almond  = local(lid_top + lid_bot)

        if openness < 0.16:
            self._strip((52, 38, 38), lid_top, 0.0030, 0.0030)
            return

        eye  = pygame.Surface((w_px, h_px), pygame.SRCALPHA)
        mask = pygame.Surface((w_px, h_px), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), almond)
        pygame.draw.polygon(eye, (252, 250, 246), almond)

        # the iris: big enough to touch both lids, dark rim, light pooling low,
        # one big soft catchlight and a small answering one
        ic  = self.spec.eye_color
        ir  = self._len(0.0175 if not male else 0.0150)
        icx = local([(ex, ey - 0.0008)])[0]
        pygame.draw.circle(eye, shade(ic, 0.40), icx, ir)
        pygame.draw.circle(eye, ic, icx, int(ir * 0.86))
        pygame.draw.circle(eye, shade(ic, 1.50), (icx[0], icx[1] + int(ir * 0.38)), int(ir * 0.52))
        pygame.draw.circle(eye, (24, 20, 24), icx, int(ir * 0.38))
        pygame.draw.circle(eye, (255, 255, 255), (icx[0] - int(ir * 0.34), icx[1] - int(ir * 0.36)),
                           int(ir * 0.30))
        pygame.draw.circle(eye, (255, 255, 255, 210), (icx[0] + int(ir * 0.44), icx[1] + int(ir * 0.42)),
                           int(ir * 0.14))
        # the upper lid's soft shadow across the top of the eye
        sh = pygame.Surface((w_px, h_px), pygame.SRCALPHA)
        pygame.draw.polygon(sh, (60, 44, 46, 55),
                            local(lid_top + [(ex + hw, ey + top_h * 1.1), (ex - hw, ey + top_h * 1.1)]))
        eye.blit(sh, (0, 0))

        eye.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.canvas.blit(eye, (ox, oy))

        # the lash: top only, soft, swelling toward the outer corner. no
        # outline anywhere else - outlines all around are what made them scary.
        lash = (52, 38, 38)
        if side > 0:
            self._strip(lash, lid_top, 0.0022, 0.0052 if not male else 0.0040)
        else:
            self._strip(lash, lid_top[::-1], 0.0022, 0.0052 if not male else 0.0040)
        if not male:
            wing_x = ex + side * hw
            self._strip(lash, [(wing_x, ey + 0.003), (wing_x + side * 0.0030, ey + 0.0052)],
                        0.0024, 0.0007)

    # -- hair ---------------------------------------------------------------------

    def _back_hair(self, hx, hy, hair, hair_dk, male):
        # volume is the whole secret: the hair rises well above the skull and
        # swells past the cheeks, or it reads as a swim cap.
        style = self.spec.hair_style
        if style == "long":
            crown = hy + 0.100
            # the dark base: a big falling mass with an s-curve to the sides
            r = bezier((hx, crown), (hx + 0.112, hy + 0.030), (hx + 0.106, 0.74))
            r += bezier((hx + 0.106, 0.74), (hx + 0.118, 0.62), (hx + 0.058, 0.520))
            l = bezier((hx, crown), (hx - 0.112, hy + 0.030), (hx - 0.106, 0.74))
            l += bezier((hx - 0.106, 0.74), (hx - 0.118, 0.62), (hx - 0.058, 0.520))
            self._poly(hair_dk, r + [(hx + 0.020, 0.512), (hx - 0.020, 0.512)] + l[::-1])
            # the body: wide ribbons overlapping into one flowing mass
            for fx, w, ln in ((-0.072, 0.052, 0.565), (-0.026, 0.056, 0.548),
                              (0.026, 0.056, 0.555), (0.072, 0.052, 0.570)):
                self._strip(hair, bezier((hx + fx * 0.45, hy + 0.062),
                                         (hx + fx * 1.35, hy - 0.060),
                                         (hx + fx, ln)), w, w * 0.5)
            self._ell(hair, (hx, hy + 0.034), 0.084, 0.072)
        elif style == "short":
            # a full bob, curling in at the jaw
            self._ell(hair_dk, (hx, hy + 0.006), 0.084, 0.088)
            self._ell(hair, (hx, hy + 0.022), 0.077, 0.074)
            for s in (-1, 1):
                self._strip(hair, bezier((hx + s * 0.068, hy + 0.024),
                                         (hx + s * 0.084, hy - 0.030),
                                         (hx + s * 0.046, hy - 0.066)), 0.030, 0.013)
        elif style == "fluffy":
            # a soft full mass, wolf-cut-ish, tufts breaking the edge
            self._ell(hair_dk, (hx, hy + 0.010), 0.086, 0.092)
            self._ell(hair, (hx, hy + 0.024), 0.078, 0.077)
            for s in (-1, 1):
                self._strip(hair, bezier((hx + s * 0.068, hy + 0.028),
                                         (hx + s * 0.088, hy - 0.026),
                                         (hx + s * 0.058, hy - 0.064)), 0.030, 0.011)
            self._ell(hair_dk, (hx, hy - 0.044), 0.044, 0.026)
        elif style == "spiky":
            for i in range(7):
                a   = math.pi * (0.10 + 0.80 * i / 6)
                tip = (hx + math.cos(a) * 0.100, hy + 0.016 + math.sin(a) * 0.104)
                bl  = (hx + math.cos(a + 0.30) * 0.054, hy + 0.016 + math.sin(a + 0.30) * 0.056)
                br  = (hx + math.cos(a - 0.30) * 0.054, hy + 0.016 + math.sin(a - 0.30) * 0.056)
                self._poly(hair_dk, [bl, tip, br])
            self._ell(hair, (hx, hy + 0.016), 0.066, 0.068)

    def _front_hair(self, hx, hy, hair, hair_dk, hair_lt, male):
        style = self.spec.hair_style
        rx    = 0.0575

        # the fringe casts a whisper of shadow high on the forehead
        self._tell((*shade(self.spec.skin, 0.72), 22), (hx, hy + 0.044), 0.040, 0.0070)

        if style == "spiky":
            for i in range(6):
                a   = math.pi * (0.22 + 0.56 * i / 5)
                tip = (hx + math.cos(a) * 0.078, hy + 0.020 + math.sin(a) * 0.080)
                bl  = (hx + math.cos(a + 0.24) * 0.044, hy + 0.026 + math.sin(a + 0.24) * 0.046)
                br  = (hx + math.cos(a - 0.24) * 0.044, hy + 0.026 + math.sin(a - 0.24) * 0.046)
                self._poly(hair, [bl, tip, br])
            self._tell((*hair_lt, 70), (hx - 0.012, hy + 0.058), 0.034, 0.013)
            return

        if style == "fluffy":
            # choppy fringe pieces split off-center, staggered so the forehead
            # breathes between them
            part = hx + 0.010
            for fx, ln, w in ((-0.048, 0.034, 0.017), (-0.020, 0.050, 0.015),
                              (0.010, 0.038, 0.014), (0.040, 0.032, 0.017)):
                self._strip(hair, bezier((part, hy + 0.072),
                                         (hx + fx * 1.2, hy + 0.058),
                                         (hx + fx, hy + ln)), w, 0.0060)
            for s in (-1, 1):
                self._strip(hair, bezier((hx + s * 0.058, hy + 0.056),
                                         (hx + s * 0.078, hy + 0.014),
                                         (hx + s * 0.062, hy - 0.030)), 0.024, 0.010)
            self._strip(hair_lt, bezier((hx - 0.034, hy + 0.072), (hx, hy + 0.080),
                                        (hx + 0.028, hy + 0.070)), 0.0055, 0.0030)
            return

        # long and short: curtain fringe from a soft middle part, like the
        # reference - two sweeps that open over the brow
        part = (hx - 0.004, hy + 0.076)
        for s in (-1, 1):
            reach = rx * (0.94 if s > 0 else 0.97)
            sweep = bezier(part, (hx + s * 0.044, hy + 0.064), (hx + s * reach, hy + 0.012))
            back  = bezier((hx + s * reach, hy + 0.012), (hx + s * 0.026, hy + 0.052), part)
            self._poly(hair, sweep + back)
            # a finer piece breaking off each curtain, like the reference's
            # little face-framing wisps
            self._strip(hair, bezier((hx + s * 0.030, hy + 0.058),
                                     (hx + s * 0.052, hy + 0.034),
                                     (hx + s * 0.044, hy + 0.004)), 0.0085, 0.0035)
        # the shine: a soft halo arc across the crown
        self._strip(hair_lt, bezier((hx - 0.052, hy + 0.052), (hx - 0.004, hy + 0.086),
                                    (hx + 0.046, hy + 0.054)), 0.0060, 0.0035)

        # face-framing pieces, s-curved, in front of the cheeks
        for s, ln in ((-1, 0.70 if male else 0.665), (1, 0.71 if male else 0.675)):
            p = bezier((hx + s * rx * 0.98, hy + 0.022),
                       (hx + s * (rx + 0.020), hy - 0.048),
                       (hx + s * (rx + 0.002), ln))
            self._strip(hair, p, 0.0200, 0.0080)
        if style == "long" and not male:
            # the long fall in front of the shoulders, s-curving out then in
            for s in (-1, 1):
                p = bezier((hx + s * rx * 0.92, hy - 0.020),
                           (hx + s * 0.104, 0.69),
                           (hx + s * 0.058, 0.560))
                self._strip(hair, p, 0.0240, 0.0110)
                q = bezier((hx + s * rx * 0.78, hy - 0.030),
                           (hx + s * 0.086, 0.71),
                           (hx + s * 0.070, 0.630))
                self._strip(hair_lt, q, 0.0048, 0.0026)

    # -- symbol -------------------------------------------------------------------

    def _draw_symbol(self, surface, center, size, color, brightness):
        self._add_to(surface, self._glow(size * 1.5, color, brightness * 0.45), center)
        shape = self.spec.symbol
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
