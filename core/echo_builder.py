"""Session Zero - first launch builds the ideal self, and quietly calibrates the brain."""

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


def _choose_path(stage):
    # the fork: a ready-made companion, or build one from scratch. returns 0 for
    # the presets, 1 for the full builder.
    options = [("pick a ready one", "five companions, ready to meet"),
               ("make your own",    "build a character from scratch - every detail yours")]
    idx = 0
    while True:
        dt, events = stage.frame()
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    idx = (idx - 1) % 2
                elif e.key in (pygame.K_RIGHT, pygame.K_e):
                    idx = (idx + 1) % 2
                elif e.key == pygame.K_RETURN:
                    return idx
        stage.say("how do you want to meet them?", 0.30)
        stage.say(options[idx][0], 0.46, stage.mid, color=(226, 230, 238))
        stage.say(options[idx][1], 0.55, stage.small, alpha=200, color=(190, 198, 212))
        stage.hint("left and right to choose   ·   enter to pick")
        pygame.display.flip()


def _make_yourself(stage):
    # the full builder: every knob the procedural renderer draws, each turned with
    # a live, breathing preview. returns the picks, ready to save into the profile.
    cb    = character_builder
    dials = [
        ("build",      "their build",       cb.BUILDS),
        ("form",       "how they carry it", cb.FORMS),
        ("hair_style", "their hair",        cb.HAIR_STYLES),
        ("hair_color", "hair colour",       cb.HAIR_COLORS),
        ("skin",       "their skin",        cb.SKIN_TONES),
        ("eye_color",  "their eyes",        cb.EYE_COLORS),
        ("outfit",     "what they wear",    cb.OUTFITS),
        ("palette",    "their light",       cb.PALETTES),
        ("symbol",     "their mark",        cb.SYMBOLS),
    ]
    idx = {key: 0 for key, _, _ in dials}
    idx["skin"] = 1                      # a gentle starting tone, not the palest
    base = cb.load_pack("gentle_guide")  # a neutral base; every field gets overridden

    def picks():
        return {key: options[idx[key]] for key, _, options in dials}

    i = 0
    while 0 <= i < len(dials):
        key, label, options = dials[i]
        advance = 0
        spec = cb.spec_from_pack(base, **picks())
        who  = cb.make_character(spec, pos=(stage.size[0] // 2, int(stage.size[1] * 0.88)),
                                 height=int(stage.size[1] * 0.48))
        who.t = stage.t
        dt, events = stage.frame()
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    idx[key] = (idx[key] - 1) % len(options)
                elif e.key in (pygame.K_RIGHT, pygame.K_e):
                    idx[key] = (idx[key] + 1) % len(options)
                elif e.key in (pygame.K_RETURN, pygame.K_DOWN):
                    advance = 1
                elif e.key in (pygame.K_BACKSPACE, pygame.K_UP) and i > 0:
                    advance = -1
        who.update(dt)
        who.draw(stage.screen)
        stage.say("make yourself.", 0.06)
        stage.say(f"{label}   ·   {idx[key] + 1} of {len(options)}", 0.135, stage.mid,
                  color=(214, 222, 234))
        back = "   ·   backspace to go back" if i > 0 else ""
        stage.hint(f"left and right to change   ·   enter when it's right{back}")
        pygame.display.flip()
        i += advance
    return picks()


def _pick_character(stage, title="who walks with you?"):
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
        stage.say(title, 0.08)
        stage.say(pack["name"], 0.80, stage.mid, color=(226, 230, 238))
        stage.say('"' + pack["voice"]["phrases"]["greeting"][0] + '"', 0.855, stage.small,
                  alpha=200, color=(190, 198, 212))
        stage.hint("left and right to meet them   enter to choose")
        pygame.display.flip()


def _customize(stage, pack):
    # make them yours. four quiet dials - build, hair, skin, and the palette
    # that becomes your light - shown live on the figure. small on purpose, day
    # one should not be a settings menu.
    builds   = character_builder.BUILDS
    styles   = character_builder.HAIR_STYLES
    tones    = character_builder.SKIN_TONES
    palettes = character_builder.PALETTES
    build_idx = builds.index(pack["visual"].get("gender", "female"))
    hair_idx  = styles.index(pack["visual"]["hair"]["style"]) \
        if pack["visual"]["hair"]["style"] in styles else 0
    idx = {"build": build_idx, "hair": hair_idx, "skin": 1, "palette": 0}
    sizes = {"build": len(builds), "hair": len(styles),
             "skin": len(tones), "palette": len(palettes)}
    for stage_name, hint in (("build",   "left and right for their build   enter when it's them"),
                             ("hair",    "left and right for their hair   enter when it's them"),
                             ("skin",    "left and right for their skin   enter when it's them"),
                             ("palette", "left and right for their light   enter when it's them")):
        while True:
            spec = character_builder.spec_from_pack(pack,
                                                    hair_style=styles[idx["hair"]],
                                                    skin=tones[idx["skin"]],
                                                    build=builds[idx["build"]],
                                                    palette=palettes[idx["palette"]])
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
    return (builds[idx["build"]], styles[idx["hair"]], tones[idx["skin"]],
            palettes[idx["palette"]])


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

    if _choose_path(stage) == 0:
        # a ready-made companion: pick one, then the four quick dials
        pack = _pick_character(stage)
        build, hair, skin, palette = _customize(stage, pack)
        character = {"pack": pack["id"], "build": build, "hair_style": hair,
                     "skin": skin, "palette": palette}
    else:
        # from scratch: build the look, then choose whose voice they have. the look
        # and the personality are picked apart, so a custom face can carry any voice.
        picks = _make_yourself(stage)
        pack  = _pick_character(stage, "and whose voice do they have?")
        character = {"pack": "custom", "voice": pack["id"], **picks}

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
        "character": character,
        "session_zero_signals": signals,
    }
    session_manager.save_profile(profile)
    _closing(stage, pack, profile)
    return profile
