"""EchoBuilder: first launch, Session Zero.

it looks like onboarding - a few quiet questions in the sky, then you choose
who walks with you and make them yours. it is also the ML brain's first
calibration: how long you wait before you start typing, how long you take,
how much you say. the signals ride along in profile.json for ml/ to read in
Layer 2. we never ask how you feel. we watch how you answer.

conversational pacing, not a form. one question at a time, the stars keep
moving, nothing is timed out, nothing is required to be profound.

writes data/profile.json
"""

import sys
import math
import datetime
import time

import pygame

from core import session_manager
from character import character_builder
from character.renderer import Character

QUESTIONS = [
    ("your_name",   "before anything else - what should i call you?"),
    ("ideal_name",  "now the version of you that made it. give them a name."),
    ("core_trait",  "one word for what they have that you want most."),
    ("value_1",     "three things they would never give up. the first?"),
    ("value_2",     "the second."),
    ("value_3",     "and the last one."),
    ("shadow_name", "the version of you at your worst - name them too. naming helps."),
    ("shadow_trait","one word for what that one does to you."),
]


def _wrap(font, text, width):
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = (line + " " + w).strip()
        if font.size(trial)[0] <= width:
            line = trial
        else:
            lines.append(line)
            line = w
    lines.append(line)
    return lines


class _Stage:
    # the shared backdrop: sky, stars, fade-in, text helpers. every step of
    # session zero draws on top of this.

    def __init__(self, screen, clock):
        from visual.worlds import Starfield, vgradient   # here to avoid a cycle at import time
        self.screen = screen
        self.clock  = clock
        self.size   = screen.get_size()
        self.sky    = vgradient(self.size, (12, 16, 34), (44, 40, 76))
        self.stars  = Starfield(self.size)
        self.big    = pygame.font.Font(None, 42)
        self.mid    = pygame.font.Font(None, 32)
        self.small  = pygame.font.Font(None, 22)
        self.t      = 0.0

    def frame(self):
        # one tick of the backdrop. returns dt and the frame's events.
        dt = self.clock.tick(60) / 1000.0
        self.t += dt
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
        self.stars.update(dt)
        self.screen.blit(self.sky, (0, 0))
        self.stars.draw(self.screen)
        return dt, events

    def say(self, text, y_frac, font=None, alpha=255, color=(232, 232, 232)):
        font = font or self.big
        y = int(self.size[1] * y_frac)
        for line in _wrap(font, text, int(self.size[0] * 0.7)):
            surf = font.render(line, True, color)
            surf.set_alpha(alpha)
            self.screen.blit(surf, (self.size[0] // 2 - surf.get_width() // 2, y))
            y += font.get_linesize()

    def hint(self, text):
        alpha = int(70 + 30 * math.sin(self.t * 1.6))
        self.say(text, 0.90, self.small, alpha)


def _ask(stage, prompt):
    # one question, one typed answer. returns (answer, signal) where signal is
    # the calibration metadata - hesitation, duration, length.
    typed   = ""
    shown   = time.monotonic()
    first   = None
    while True:
        dt, events = stage.frame()
        for e in events:
            if e.type == pygame.KEYDOWN:
                if first is None and e.key not in (pygame.K_RETURN, pygame.K_ESCAPE):
                    first = time.monotonic()
                if e.key == pygame.K_RETURN and typed.strip():
                    now = time.monotonic()
                    return typed.strip(), {
                        "hesitation_s": round((first or now) - shown, 2),
                        "duration_s":   round(now - shown, 2),
                        "length":       len(typed.strip()),
                    }
                elif e.key == pygame.K_BACKSPACE:
                    typed = typed[:-1]
                elif e.unicode and e.unicode.isprintable() and len(typed) < 40:
                    typed += e.unicode
        stage.say(prompt, 0.30)
        cursor = "_" if int(stage.t * 2) % 2 == 0 else " "
        stage.say(typed + cursor, 0.46, stage.mid, color=(214, 222, 234))
        stage.hint("enter when ready. there are no wrong answers here.")
        pygame.display.flip()


def _pick_character(stage):
    # the five of them, side by side, breathing. left/right to meet them,
    # enter to choose. returns the chosen pack dict.
    packs = character_builder.all_packs()
    w     = stage.size[0]
    row_y = int(stage.size[1] * 0.74)
    cast  = []
    for i, pack in enumerate(packs):
        x = int(w * (0.5 + (i - 2) * 0.17))
        cast.append(character_builder.make_character(character_builder.spec_from_pack(pack),
                                                     pos=(x, row_y), height=int(stage.size[1] * 0.30)))
    idx = 0
    while True:
        dt, events = stage.frame()
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    idx = (idx - 1) % len(packs)
                elif e.key in (pygame.K_RIGHT, pygame.K_e):
                    idx = (idx + 1) % len(packs)
                elif e.key == pygame.K_RETURN:
                    return packs[idx]
        for i, who in enumerate(cast):
            who.set_expression("happy" if i == idx else "neutral")
            who.update(dt)
            who.draw(stage.screen)
        pack = packs[idx]
        stage.say("who walks with you?", 0.08)
        stage.say(pack["name"], 0.80, stage.mid, color=(226, 230, 238))
        stage.say('"' + pack["voice"]["phrases"]["greeting"][0] + '"', 0.855, stage.small,
                  alpha=200, color=(190, 198, 212))
        stage.hint("left and right to meet them   enter to choose")
        pygame.display.flip()


def _customize(stage, pack):
    # make them yours. three quiet dials - build, hair, skin - shown live on
    # the figure. small on purpose, day one should not be a settings menu.
    builds   = character_builder.BUILDS
    styles   = character_builder.HAIR_STYLES
    tones    = character_builder.SKIN_TONES
    build_idx = builds.index(pack["visual"].get("gender", "female"))
    hair_idx  = styles.index(pack["visual"]["hair"]["style"]) \
        if pack["visual"]["hair"]["style"] in styles else 0
    skin_idx  = 1
    idx = {"build": build_idx, "hair": hair_idx, "skin": skin_idx}
    sizes = {"build": len(builds), "hair": len(styles), "skin": len(tones)}
    for stage_name, hint in (("build", "left and right for their build   enter when it's them"),
                             ("hair", "left and right for their hair   enter when it's them"),
                             ("skin", "left and right for their skin   enter when it's them")):
        while True:
            spec = character_builder.spec_from_pack(pack,
                                                    hair_style=styles[idx["hair"]],
                                                    skin=tones[idx["skin"]],
                                                    build=builds[idx["build"]])
            who  = character_builder.make_character(
                spec, pos=(stage.size[0] // 2, int(stage.size[1] * 0.82)),
                height=int(stage.size[1] * 0.42))
            who.t = stage.t
            done = False
            dt, events = stage.frame()
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_LEFT, pygame.K_a):
                        idx[stage_name] = (idx[stage_name] - 1) % sizes[stage_name]
                    elif e.key in (pygame.K_RIGHT, pygame.K_e):
                        idx[stage_name] = (idx[stage_name] + 1) % sizes[stage_name]
                    elif e.key == pygame.K_RETURN:
                        done = True
            who.update(dt)
            who.draw(stage.screen)
            stage.say("make them yours.", 0.08)
            stage.hint(hint)
            pygame.display.flip()
            if done:
                break
    return builds[idx["build"]], styles[idx["hair"]], tones[idx["skin"]]


def _closing(stage, pack, profile):
    # the chosen one says hello, properly this time. a breath, then the world.
    spec = character_builder.spec_from_profile(profile)
    who  = character_builder.make_character(
        spec, pos=(stage.size[0] // 2, int(stage.size[1] * 0.84)),
        height=int(stage.size[1] * 0.44))
    who.set_expression("happy")
    waited = 0.0
    while waited < 3.2:
        dt, events = stage.frame()
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                return
        waited += dt
        who.update(dt)
        who.draw(stage.screen)
        stage.say('"' + pack["voice"]["phrases"]["greeting"][1] + '"', 0.16, stage.mid,
                  color=(222, 226, 236))
        pygame.display.flip()


def run_builder(screen, clock):
    # the whole of session zero. returns the saved profile.
    stage   = _Stage(screen, clock)
    answers = {}
    signals = []
    for key, prompt in QUESTIONS:
        answer, signal = _ask(stage, prompt)
        answers[key]   = answer
        signal["key"]  = key
        signals.append(signal)

    pack              = _pick_character(stage)
    build, hair, skin = _customize(stage, pack)

    profile = {
        "created":   datetime.date.today().isoformat(),
        "your_name": answers["your_name"],
        "ideal_self": {
            "name":       answers["ideal_name"],
            "core_trait": answers["core_trait"],
            "values":     [answers["value_1"], answers["value_2"], answers["value_3"]],
        },
        "shadow_self": {
            "name":  answers["shadow_name"],
            "trait": answers["shadow_trait"],
        },
        "character": {"pack": pack["id"], "build": build, "hair_style": hair, "skin": skin},
        "session_zero_signals": signals,
    }
    session_manager.save_profile(profile)
    _closing(stage, pack, profile)
    return profile
