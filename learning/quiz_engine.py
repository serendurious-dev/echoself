"""the lesson session: the glowing panel, the quiz, the live reactions, the two voices."""

import time
import math
import random

import pygame

from learning import codepath, progress_tracker, mastery

HESITATION_S = 14.0    # the default, before the psychology layer has a say

DEFAULT_PLAN = dict(state=None, mode=None, expression="neutral",
                    opening_slot="greeting", hesitation_s=HESITATION_S)


def wrap_text(font, text, width):
    lines = []
    for raw in text.split("\n"):
        words, line = raw.split(), ""
        if not words:
            lines.append("")
        for w in words:
            trial = (line + " " + w).strip()
            if font.size(trial)[0] <= width:
                line = trial
            else:
                lines.append(line)
                line = w
        if words:
            lines.append(line)
    return lines


class LessonSession:
    # one user working through one track, lesson by lesson. the world owns
    # drawing the sky and the character, this owns the panel and the flow.

    def __init__(self, track, character, voice, plan=None):
        self.track     = track
        self.character = character
        self.voice     = voice
        self.plan      = dict(DEFAULT_PLAN, **(plan or {}))
        # spaced repetition: a question missed in an earlier session comes back
        # first, in the character's voice, before any new lesson. if there's
        # nothing owed, we go straight to the next lesson.
        self.reviewing = False
        review = codepath.review_lesson(track)
        if review is not None:
            self.reviewing = True
            self.lesson    = review
        else:
            self.lesson = codepath.next_lesson(track)
        self.state     = "reading" if self.lesson else "track_done"
        self._load_exercises()
        self.typed     = ""
        self.hints     = 0
        self.feedback  = None
        self.pair      = None     # the (teacher, friend) two-voice response, on a miss
        self.shown_at  = time.monotonic()
        self.nudged    = False

        # the psychology layer's plan, acted on: her resting face for the day,
        # and the line that opens the session - her own memory of you when the
        # state asks for it, her voice otherwise
        self.character.set_expression(self.plan["expression"])
        if self.reviewing:
            self.opening = "you missed this one before. let's try it again - I remembered."
        else:
            self.opening = (self.plan.get("memory_line") or self.plan.get("mirror_line")
                            or random.choice(self.voice[self.plan["opening_slot"]]))
            # if you've been away a while, she welcomes you back first - no guilt,
            # just glad you're here. presence over pressure, in the learning world too.
            welcome = mastery.welcome_back_line(self.track)
            if welcome:
                self.opening = welcome + " " + self.opening

        self.font      = pygame.font.Font(None, 26)
        self.font_big  = pygame.font.Font(None, 34)
        self.font_code = pygame.font.SysFont("consolas,courier", 22)
        self.font_soft = pygame.font.Font(None, 22)

    # -- voice ----------------------------------------------------------------

    def _line(self, slot):
        return random.choice(self.voice[slot])

    def _voice_line(self, slot):
        # teacher / friend banks may be missing on an old or sparse pack
        lines = self.voice.get(slot)
        return random.choice(lines) if lines else None

    # -- flow -----------------------------------------------------------------

    def _load_exercises(self):
        # the lesson's exercises, and a pointer to the one we're on
        self.exercises = codepath.lesson_exercises(self.lesson) if self.lesson else []
        self.ex_i = 0
        self.ex   = self.exercises[0] if self.exercises else None

    def _advance(self):
        # next exercise in this lesson, or the lesson's done
        if self.ex_i + 1 < len(self.exercises):
            self.ex_i += 1
            self.ex   = self.exercises[self.ex_i]
            self._begin_question()
        else:
            self._finish_lesson()

    def _begin_question(self):
        self.state    = "question"
        self.typed    = ""
        self.hints    = 0
        self.feedback = None
        self.pair     = None
        self.shown_at = time.monotonic()
        self.nudged   = False
        self.character.set_expression("neutral")

    def _check(self, answer_text=None, choice=None):
        quiz    = self.ex
        elapsed = int(time.monotonic() - self.shown_at)
        if quiz["type"] == "fill_blank":
            right = answer_text.strip().lower() == str(quiz["answer"]).strip().lower()
        else:
            right = choice == quiz["answer_index"]
        progress_tracker.log_event(self.track, self.lesson["cluster"], self.lesson["id"],
                                   "quiz", correct="yes" if right else "no",
                                   hints_used=self.hints, duration_s=elapsed)
        if right and self.reviewing:
            # the missed question is mended; the wrong answer that haunted the
            # log is now answered right, so it leaves the review pool. straight
            # on to the real next lesson, no second "lesson done" logged.
            self.reviewing = False
            self.pair      = None
            self.lesson    = codepath.next_lesson(self.track)
            self.state     = "reading" if self.lesson else "track_done"
            self._load_exercises()
            self.feedback  = None
            self.opening   = "there. that one's yours now. onward."
            self.character.set_expression("happy")
        elif right:
            self.state    = "done"
            self.feedback = self._line("correct")
            self.pair     = None
            self.character.set_expression("celebrating")
        else:
            # the two voices answer together: the teacher's firm truth, then the
            # friend's grounding. AlterEgo's idea, in the character's own voice.
            self.feedback = self._line("incorrect")
            self.pair     = (self._voice_line("teacher"), self._voice_line("friend"))
            self.typed    = ""
            self.character.set_expression("patient")

    def _finish_lesson(self):
        progress_tracker.log_event(self.track, self.lesson["cluster"], self.lesson["id"],
                                   "lesson_done")
        self.lesson = codepath.next_lesson(self.track)
        self._load_exercises()
        if self.lesson is None:
            self.state = "track_done"
            self.character.set_expression("happy")
        else:
            self.state = "reading"
            self.character.set_expression("neutral")

    # -- input ----------------------------------------------------------------

    def handle(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.state == "reading":
            if event.key == pygame.K_RETURN:
                self._begin_question()
        elif self.state == "question":
            quiz = self.ex
            if event.key == pygame.K_h and self.hints < len(self.ex["hints"]):
                self.hints += 1
                self.feedback = None
                self.pair     = None
                progress_tracker.log_event(self.track, self.lesson["cluster"],
                                           self.lesson["id"], "hint",
                                           hints_used=self.hints)
            elif quiz["type"] == "fill_blank":
                if event.key == pygame.K_RETURN and self.typed.strip():
                    self._check(answer_text=self.typed)
                elif event.key == pygame.K_BACKSPACE:
                    self.typed = self.typed[:-1]
                elif event.unicode and event.unicode.isprintable() and len(self.typed) < 30:
                    self.typed += event.unicode
            else:
                if pygame.K_1 <= event.key <= pygame.K_4:
                    choice = event.key - pygame.K_1
                    if choice < len(quiz["options"]):
                        self._check(choice=choice)
        elif self.state == "done":
            if event.key == pygame.K_RETURN:
                self._advance()

    # -- time -----------------------------------------------------------------

    def update(self, dt):
        # hesitation: noticed once, gently, never repeated for the same
        # question. the window is the plan's - drift has already shaped it.
        if (self.state == "question" and not self.nudged
                and time.monotonic() - self.shown_at > self.plan["hesitation_s"]):
            self.nudged   = True
            self.feedback = self._line("hesitation")
            self.character.set_expression("patient")

    # -- drawing ----------------------------------------------------------------

    def draw(self, surface):
        w, h  = surface.get_size()
        panel = pygame.Rect(int(w * 0.46), int(h * 0.08), int(w * 0.50), int(h * 0.80))

        # the glow behind the panel, then the glass itself
        glow = pygame.Surface((panel.w + 40, panel.h + 40))
        accent = self.character.spec.palette[0]
        pygame.draw.rect(glow, tuple(c // 5 for c in accent), glow.get_rect(), border_radius=26)
        surface.blit(glow, (panel.x - 20, panel.y - 20), special_flags=pygame.BLEND_RGB_ADD)
        glass = pygame.Surface(panel.size, pygame.SRCALPHA)
        glass.fill((10, 20, 26, 216))
        pygame.draw.rect(glass, (*accent, 70), glass.get_rect(), width=2, border_radius=14)
        surface.blit(glass, panel.topleft)

        x = panel.x + 28
        y = panel.y + 24
        inner = panel.w - 56

        # which language you're in, and how to change it (the switch lives in g)
        from learning import mastery
        self._text(surface, self.font_soft, mastery.track_name(self.track) + "    -    g to switch language",
                   x, y, inner, (150, 160, 172))
        y += self.font_soft.get_linesize() + 8

        if self.state == "track_done":
            from core import enough
            y = self._text(surface, self.font_big, "that is everything i have for now.",
                           x, y + 40, inner, (230, 232, 238))
            y = self._text(surface, self.font, self._line("farewell"), x, y + 14, inner,
                           (188, 196, 208))
            # the day's "enough" verdict, in the character's keeping
            y = self._text(surface, self.font, enough.verdict()["line"], x, y + 16, inner,
                           (206, 198, 172))
            return

        lesson = self.lesson
        y = self._text(surface, self.font_big, lesson["title"], x, y, inner, (232, 234, 240))
        y += 12

        if self.state == "reading" and self.opening:
            y = self._text(surface, self.font_soft, '"' + self.opening + '"', x, y, inner,
                           (186, 178, 156))
            y += 10

        if self.state == "reading":
            y = self._text(surface, self.font, lesson["concept"], x, y, inner, (208, 216, 226))
            y += 10
            y = self._text(surface, self.font, lesson["explanation"], x, y, inner, (178, 188, 200))
            y += 14
            y = self._code(surface, lesson["code_example"], x, y, inner)
            footer = "enter - try the question"
            if self.plan.get("offer_drift"):
                footer += "      (or tab, then d - the sky is there if today is heavy)"
            self._text(surface, self.font_soft, footer, x, panel.bottom - 40, inner,
                       (140, 150, 162))
        else:
            quiz = self.ex
            if len(self.exercises) > 1:
                y = self._text(surface, self.font_soft,
                               f"question {self.ex_i + 1} of {len(self.exercises)}",
                               x, y, inner, (150, 160, 172))
                y += 4
            y = self._text(surface, self.font, quiz["question"], x, y, inner, (214, 220, 230))
            y += 10
            if quiz["type"] == "fill_blank":
                cursor = "_" if int(time.monotonic() * 2) % 2 == 0 else " "
                y = self._text(surface, self.font_code, "> " + self.typed + cursor, x, y,
                               inner, (222, 228, 236))
            else:
                for i, option in enumerate(quiz["options"]):
                    color = (222, 228, 236) if self.state == "question" else (150, 158, 170)
                    y = self._text(surface, self.font, f"{i + 1}.  {option}", x, y, inner, color)
                    y += 4
            y += 10
            for i in range(self.hints):
                y = self._text(surface, self.font_soft, "hint: " + self.ex["hints"][i],
                               x, y, inner, (168, 180, 156))
                y += 4
            if self.feedback:
                y += 8
                y = self._text(surface, self.font, self.feedback, x, y, inner, (210, 200, 170))
            if self.pair:
                # the two voices: the teacher's firm line, then the friend's warm one
                teacher, friend = self.pair
                if teacher:
                    y += 8
                    y = self._text(surface, self.font_soft, teacher, x, y, inner, (214, 198, 168))
                if friend:
                    y += 4
                    y = self._text(surface, self.font_soft, friend, x, y, inner, (176, 200, 188))
            if self.state == "question":
                left = len(self.ex["hints"]) - self.hints
                more = f"h - hint ({left} left)   " if left else ""
                what = "type and enter" if quiz["type"] == "fill_blank" else "answer with 1-4"
                self._text(surface, self.font_soft, f"{what}   {more}", x,
                           panel.bottom - 40, inner, (140, 150, 162))
            else:
                self._text(surface, self.font_soft, "enter - next", x,
                           panel.bottom - 40, inner, (140, 150, 162))

    def _text(self, surface, font, text, x, y, width, color):
        for line in wrap_text(font, text, width):
            surface.blit(font.render(line, True, color), (x, y))
            y += font.get_linesize()
        return y

    def _code(self, surface, code, x, y, width):
        lines = code.split("\n")
        pad   = 12
        box_h = len(lines) * self.font_code.get_linesize() + pad * 2
        box   = pygame.Surface((width, box_h), pygame.SRCALPHA)
        box.fill((4, 10, 14, 200))
        surface.blit(box, (x, y))
        cy = y + pad
        for line in lines:
            surface.blit(self.font_code.render(line, True, (190, 214, 200)), (x + pad, cy))
            cy += self.font_code.get_linesize()
        return y + box_h
