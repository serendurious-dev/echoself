"""the three worlds (ambient / learning / drift), the fade between them, and the main loop."""

import math
import random

import pygame

from character.renderer import Character, gentle_guide

FPS          = 60
WINDOW_SIZE  = (1280, 720)
FADE_SECONDS = 0.7   # full out-and-in. long enough to feel soft, short enough to not annoy


def vgradient(size, top, bottom):
    # paint a 1x2 column and let smoothscale do the blending. cheap and looks fine.
    column = pygame.Surface((1, 2))
    column.set_at((0, 0), top)
    column.set_at((0, 1), bottom)
    return pygame.transform.smoothscale(column, size)


def blend(a, b, t):
    # a moved toward b by t
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Starfield:
    # one sky's worth of stars, shared between the worlds. three depth bands
    # moving at different speeds, which is what makes a flat screen feel deep.

    def __init__(self, size, tint=(232, 220, 200), count=110):
        self.size = size
        self.tint = tint
        w, h = size
        self.stars = [dict(x=random.uniform(0, w),
                           y=random.uniform(0, h * 0.82),
                           depth=random.choice((0.35, 0.65, 1.0)),
                           size=random.choice((1, 1, 1, 2)),
                           phase=random.uniform(0, math.tau))
                      for _ in range(count)]
        self.t = 0.0
        self._shooting = None
        self._next_fall = random.uniform(14.0, 30.0)

    def update(self, dt, speed=1.0):
        self.t += dt
        w = self.size[0]
        for s in self.stars:
            s["x"] -= 2.4 * s["depth"] * speed * dt    # the deep ones barely move
            if s["x"] < -2:
                s["x"] = w + 2
                s["y"] = random.uniform(0, self.size[1] * 0.82)

        # now and then, one falls. it asks nothing of you.
        if self._shooting is None:
            self._next_fall -= dt
            if self._next_fall <= 0:
                x = random.uniform(w * 0.2, w * 0.9)
                y = random.uniform(40, self.size[1] * 0.35)
                self._shooting = dict(x=x, y=y, life=0.0)
        else:
            self._shooting["life"] += dt
            if self._shooting["life"] > 0.9:
                self._shooting = None
                self._next_fall = random.uniform(14.0, 30.0)

    def draw(self, surface, brightness=1.0):
        for s in self.stars:
            tw = 0.55 + 0.45 * math.sin(self.t * 1.3 + s["phase"])
            f  = tw * s["depth"] * brightness
            c  = (int(self.tint[0] * f), int(self.tint[1] * f), int(self.tint[2] * f))
            if s["size"] == 1:
                surface.set_at((int(s["x"]), int(s["y"])), c)
            else:
                pygame.draw.circle(surface, c, (int(s["x"]), int(s["y"])), 1)

        sh = self._shooting
        if sh is not None:
            # bright early, fading as it goes, a short tail behind it
            f = max(0.0, 1.0 - sh["life"] / 0.9) * brightness
            x = sh["x"] + sh["life"] * 220
            y = sh["y"] + sh["life"] * 130
            c = (int(240 * f), int(232 * f), int(210 * f))
            pygame.draw.line(surface, c, (int(x - 26), int(y - 15)), (int(x), int(y)), 1)


class World:
    # base class. a world draws itself and reacts, the manager owns the loop.
    name = "world"

    def __init__(self, size):
        self.size = size

    def enter(self):
        pass

    def exit(self):
        pass

    def handle(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


class SkyWorld(World):
    # a gradient sky tinted by the character's palette, the shared stars, a
    # horizon of the character's light, and the character standing in it.

    star_speed = 1.0     # echo distance will drive this in Layer 2
    star_brightness = 1.0
    caption = None

    def __init__(self, size, name, top, bottom, stars,
                 character=None, char_pos=None, mood="neutral"):
        super().__init__(size)
        self.name      = name
        self.sky       = vgradient(size, top, bottom)
        self.stars     = stars
        self.character = character
        self.char_pos  = char_pos or (size[0] // 2, int(size[1] * 0.88))
        self.mood      = mood
        self.font      = pygame.font.Font(None, 22)
        self.pulse     = 0.0
        # the horizon: a wide pool of the character's light, low and behind them
        accent = character.spec.palette[0] if character else (127, 181, 168)
        self._horizon = self._make_horizon(size, accent)

    @staticmethod
    def _make_horizon(size, accent):
        band = pygame.Surface((64, 32))
        for i in range(16, 0, -1):
            f = ((16 - i) / 16.0) ** 2 * 0.55
            c = (int(accent[0] * f), int(accent[1] * f), int(accent[2] * f))
            pygame.draw.ellipse(band, c, (32 - i * 2, 16 - i, i * 4, i * 2))
        return pygame.transform.smoothscale(band, (int(size[0] * 1.1), int(size[1] * 0.36)))

    def enter(self):
        if self.character:
            self.character.pos = self.char_pos
            self.character.set_expression(self.mood)

    def update(self, dt):
        self.pulse += dt
        self.stars.update(dt, self.star_speed)
        if self.character:
            self.character.update(dt)

    def draw(self, surface):
        surface.blit(self.sky, (0, 0))
        self.stars.draw(surface, self.star_brightness)
        surface.blit(self._horizon,
                     (int(self.size[0] / 2 - self._horizon.get_width() / 2),
                      int(self.size[1] - self._horizon.get_height() * 0.62)),
                     special_flags=pygame.BLEND_RGB_ADD)
        if self.character:
            self.character.draw(surface)
        if self.caption:
            # a quiet hint, breathing in the corner. drift mode has none at all.
            alpha = int(60 + 30 * math.sin(self.pulse * 1.4))
            text  = self.font.render(self.caption, True, (225, 225, 225))
            text.set_alpha(alpha)
            surface.blit(text, (22, self.size[1] - 34))


class AmbientWorld(SkyWorld):
    caption = ("t talk   tab learn   c code   e how far   p memory   "
               "l letters   v vault   d drift   esc quit")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._moment   = None     # the Echo Moment sentence currently surfacing
        self._wait     = 9.0      # until the first one
        self._show     = 0.0
        self._momfont  = pygame.font.Font(None, 30)

    def update(self, dt):
        super().update(dt)
        if self._moment is None:
            self._wait -= dt
            if self._wait <= 0:
                from core import echo_exchange
                self._moment = echo_exchange.random_sentence()
                self._show   = 8.0
                if self._moment is None:
                    self._wait = 30.0
        else:
            self._show -= dt
            if self._show <= 0:
                self._moment = None
                self._wait   = random.uniform(32, 55)

    def draw(self, surface):
        super().draw(surface)
        if not self._moment:
            return
        # an Echo Moment: a community sentence fading softly in and out
        fade  = min(1.0, (8.0 - self._show) / 1.5, self._show / 1.5)
        alpha = int(160 * max(0.0, fade))
        words, lines, line = self._moment.split(), [], ""
        for word in words:
            trial = (line + " " + word).strip()
            if self._momfont.size(trial)[0] <= self.size[0] * 0.6:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
        y = int(self.size[1] * 0.17)
        for ln in lines:
            surf = self._momfont.render(ln, True, (216, 210, 226))
            surf.set_alpha(alpha)
            surface.blit(surf, (self.size[0] // 2 - surf.get_width() // 2, y))
            y += 34


class LearningWorld(SkyWorld):
    # the character teaches here. the lesson session owns the panel and the
    # flow, this world owns the sky around it. number keys, typing and h all
    # belong to the lesson, so this world captures input - tab leaves.
    caption = "tab - back to the sky"
    star_speed = 0.6
    star_brightness = 0.7
    capture_input = True

    def __init__(self, *args, voice=None, plan=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.voice   = voice
        self.plan    = plan
        self.session = None

    def enter(self):
        super().enter()
        from learning.quiz_engine import LessonSession
        # a fresh session each visit picks up wherever the log says you are,
        # carrying the psychology layer's plan for today
        self.session = LessonSession("python", self.character, self.voice, plan=self.plan)

    def handle(self, event):
        if self.session:
            self.session.handle(event)

    def update(self, dt):
        super().update(dt)
        if self.session:
            self.session.update(dt)

    def draw(self, surface):
        super().draw(surface)
        if self.session:
            self.session.draw(surface)


class DriftWorld(SkyWorld):
    # zero UI. no caption, no numbers, nothing that could feel like a demand.
    caption = None
    star_speed = 0.35
    star_brightness = 0.55


def default_worlds(size, plan=None):
    # one character, one sky full of stars - shared. the worlds change the
    # light around them, not the person or the stars. the character is whoever
    # the profile says, the gentle guide until session zero has happened.
    # plan is the psychology layer's read of today, None means neutral.
    from core.session_manager import load_profile
    from character.character_builder import spec_from_profile, voice_from_profile, make_character
    profile = load_profile()
    spec    = spec_from_profile(profile) if profile else gentle_guide()
    voice   = voice_from_profile(profile)
    who     = make_character(spec, height=int(size[1] * 0.42))
    mood    = plan["expression"] if plan else "neutral"
    accent = who.spec.palette[0]
    stars  = Starfield(size, tint=blend((232, 220, 200), accent, 0.25))
    night  = (10, 14, 30)
    dusk   = (40, 36, 70)
    cx, cy = size[0] // 2, int(size[1] * 0.88)
    return {
        "ambient":  AmbientWorld(size, "ambient",
                                 blend(night, accent, 0.16), blend(dusk, accent, 0.30),
                                 stars, character=who, char_pos=(cx, cy), mood=mood),
        "learning": LearningWorld(size, "learning",
                                  blend((8, 16, 22), accent, 0.22), blend((26, 58, 62), accent, 0.30),
                                  stars, character=who, char_pos=(int(size[0] * 0.24), cy),
                                  voice=voice, plan=plan),
        "drift":    DriftWorld(size, "drift",
                               blend((6, 8, 18), accent, 0.09), blend((22, 24, 44), accent, 0.18),
                               stars, character=who, char_pos=(cx, cy + 10), mood="drift"),
    }


class WorldManager:
    # owns which world is alive and the fade between them. switching mid-fade just
    # retargets, you can never get stuck between worlds.

    def __init__(self, size, worlds=None):
        self.worlds  = worlds or default_worlds(size)
        self.current = self.worlds["ambient"]
        self.pending = None     # world we are fading toward
        self.fade    = 0.0      # 0 = clear, 1 = fully dark (swap happens at 1)
        self.rising  = False    # fade direction
        self.before_drift = None
        self._veil   = pygame.Surface(size)
        self._veil.fill((0, 0, 0))
        self.current.enter()

    def switch(self, name):
        target = self.worlds[name]
        if target is self.current and self.pending is None:
            return
        self.pending = target
        self.rising  = True

    def toggle_drift(self):
        # drift is one keypress away from anywhere, and the same key brings you back
        if self.current is self.worlds["drift"]:
            self.switch((self.before_drift or self.worlds["ambient"]).name)
        else:
            self.before_drift = self.current
            self.switch("drift")

    def handle(self, event):
        self.current.handle(event)

    def update(self, dt):
        speed = 2.0 / FADE_SECONDS   # half the time out, half back in
        if self.rising:
            self.fade = min(1.0, self.fade + speed * dt)
            if self.fade >= 1.0 and self.pending is not None:
                # the swap, hidden in the dark
                self.current.exit()
                self.current = self.pending
                self.pending = None
                self.current.enter()
                self.rising = False
        elif self.fade > 0.0:
            self.fade = max(0.0, self.fade - speed * dt)
        self.current.update(dt)

    def draw(self, surface):
        self.current.draw(surface)
        if self.fade > 0.0:
            self._veil.set_alpha(int(self.fade * 255))
            surface.blit(self._veil, (0, 0))


def run(args=None):
    # the loop. fixed target of 60fps, dt-based updates so a slow frame never
    # teleports an animation. first launch runs session zero before anything.
    from core.session_manager import load_profile
    from core.echo_builder import run_builder

    # --demo runs in a sandboxed data_demo/ dir, seeded with a lived-in month,
    # so the slow features have something to show. --timelapse adds a day each run.
    if getattr(args, "demo", False):
        from core import demo_mode
        demo_mode.use_demo_dir()
        demo_mode.ensure_seeded()
        if getattr(args, "timelapse", False):
            demo_mode.advance_day()

    # clean up after any unclean exit before we touch the data
    from osutil import recovery
    from core import datastore
    recovery.audit(datastore.DATA_DIR)

    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("EchoSelf")
    clock  = pygame.time.Clock()

    if load_profile() is None:
        run_builder(screen, clock)
    profile = load_profile()

    # the one thing we ask directly, once a day: a word and a number.
    from core.session_manager import logged_today
    if not logged_today():
        from core.daily import capture_mood
        capture_mood(screen, clock, profile)

    # the inner world wakes: read the logs, classify the state, get the plan.
    # this is also where the drift nudges, one small step per launch.
    from ml.behavioral_model import wake
    from ml.psychology_layer import plan_for
    from core.narrative_engine import dark_days_active
    plan = plan_for(wake())

    # a low-mood streak overrides everything toward presence - no pushing.
    if dark_days_active():
        plan["expression"]  = "drift"
        plan["offer_drift"] = True
        plan["dark_days"]   = True

    # the monthly letter, written quietly so it's waiting when you look for it
    from core import letters
    if letters.due():
        letters.write_monthly(profile)

    worlds = WorldManager(WINDOW_SIZE, default_worlds(WINDOW_SIZE, plan))

    # the soundscape: a drone warmed by how close the Echo Distance is
    from core import echo_distance
    from audio.soundscape import Soundscape
    sound = Soundscape()
    sound.start()
    sound.set_closeness(1.0 - sum(echo_distance.compute(profile).values()) / 4.0)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        # worlds that take typing (the lesson panel) get the keys first, only
        # esc and tab stay global there. everywhere else d is one keypress.
        captured = getattr(worlds.current, "capture_input", False)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_TAB:
                    worlds.switch("ambient" if worlds.current.name == "learning" else "learning")
                elif event.key == pygame.K_d and not captured:
                    worlds.toggle_drift()
                elif event.key == pygame.K_e and not captured:
                    # the Echo Distance view - radar, timeline, the mirror report
                    from visual.analytics_charts import show_echo_distance
                    accent = worlds.current.character.spec.palette[0]
                    show_echo_distance(screen, clock, profile, accent)
                elif event.key == pygame.K_t and not captured:
                    from visual.screens import talk
                    talk(screen, clock, worlds.current.character)
                    worlds.current.character.set_expression(plan["expression"] if plan else "neutral")
                elif event.key == pygame.K_c and not captured:
                    from visual.screens import run_challenge
                    from character.character_builder import voice_from_profile
                    run_challenge(screen, clock, worlds.current.character,
                                  voice_from_profile(profile))
                elif event.key == pygame.K_l and not captured:
                    from visual.screens import show_letters
                    show_letters(screen, clock, profile)
                elif event.key == pygame.K_v and not captured:
                    from visual.screens import open_vault
                    open_vault(screen, clock)
                elif event.key == pygame.K_p and not captured:
                    # what she remembers about you - the portrait, yours to read and prune
                    from visual.screens import show_portrait
                    show_portrait(screen, clock)
                elif event.key == pygame.K_m and not captured:
                    sound.toggle_mute()
                else:
                    worlds.handle(event)
            else:
                worlds.handle(event)
        worlds.update(dt)
        worlds.draw(screen)
        pygame.display.flip()

    sound.stop()
    pygame.quit()
    return 0
