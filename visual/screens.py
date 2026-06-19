"""full-screen views that pause the worlds: the challenge, the Letters, the Vault."""

import os
import random

import pygame

BG   = (10, 14, 28)
INK  = (210, 214, 224)
SOFT = (150, 158, 172)
WARM = (206, 198, 172)


def _font(size):
    return pygame.font.Font(None, size)


def _wrap(font, text, width):
    lines = []
    for raw in text.split("\n"):
        words, line = raw.split(), ""
        if not words:
            lines.append("")
            continue
        for w in words:
            trial = (line + " " + w).strip()
            if font.size(trial)[0] <= width:
                line = trial
            else:
                lines.append(line)
                line = w
        lines.append(line)
    return lines


def _scroll_text(screen, clock, title, body):
    w, h   = screen.get_size()
    font   = _font(24)
    tfont  = _font(36)
    lines  = _wrap(font, body, w - 120)
    step   = font.get_linesize()
    top    = 0
    page   = (h - 160) // step
    while True:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_q):
                    return
                if e.key in (pygame.K_DOWN, pygame.K_SPACE):
                    top = min(max(0, len(lines) - page), top + 3)
                if e.key == pygame.K_UP:
                    top = max(0, top - 3)
        screen.fill(BG)
        screen.blit(tfont.render(title, True, INK), (60, 40))
        y = 100
        for ln in lines[top:top + page]:
            screen.blit(font.render(ln, True, INK), (60, y))
            y += step
        screen.blit(font.render("up / down to read   esc to close", True, SOFT), (60, h - 44))
        pygame.display.flip()


def _ask_line(screen, clock, prompt, masked=False):
    # one line of typed input. returns the string, or None if cancelled.
    w, h  = screen.get_size()
    font  = _font(30)
    pfont = _font(30)
    typed = ""
    while True:
        t = clock.tick(60) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return None
                if e.key == pygame.K_RETURN:
                    return typed.strip() if typed.strip() else None
                if e.key == pygame.K_BACKSPACE:
                    typed = typed[:-1]
                elif e.unicode and e.unicode.isprintable() and len(typed) < 60:
                    typed += e.unicode
        screen.fill(BG)
        screen.blit(pfont.render(prompt, True, INK), (60, h // 2 - 60))
        shown  = ("-" * len(typed)) if masked else typed
        cursor = "_" if int(pygame.time.get_ticks() / 500) % 2 == 0 else " "
        screen.blit(font.render(shown + cursor, True, WARM), (60, h // 2))
        screen.blit(_font(22).render("enter to confirm   esc to cancel", True, SOFT),
                    (60, h - 44))
        pygame.display.flip()


def _flash(screen, clock, message, seconds=1.6):
    w, h = screen.get_size()
    font = _font(30)
    waited = 0.0
    while waited < seconds:
        waited += clock.tick(60) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                return
        screen.fill(BG)
        screen.blit(font.render(message, True, INK),
                    (60, h // 2 - 16))
        pygame.display.flip()


# -- the public screens -------------------------------------------------------

def show_letters(screen, clock, profile):
    from core import letters
    items = letters.all_letters()
    if not items:
        _scroll_text(screen, clock, "Letters",
                     "No letters yet.\n\nThe first one comes at the turn of the month - a letter "
                     "from the version of you that made it, looking back over the weeks. It will "
                     "be waiting here when it's time.")
        return
    body = letters.read(items[0][1])
    _scroll_text(screen, clock, f"Letter - {items[0][0]}", body)


def run_challenge(screen, clock, character, voice):
    # the editor-handoff coding challenge: write a starter file, the user solves
    # it in their own editor, we run it and the character reacts.
    from learning import codepath, challenge_runner, progress_tracker
    item = codepath.next_challenge("python")
    if item is None:
        _scroll_text(screen, clock, "Nothing to code yet",
                     "Finish a cluster's five lessons in the Learning World and its challenge "
                     "unlocks here - real code, written in your own editor.\n\nKeep going (tab), "
                     "then come back.")
        return

    path = challenge_runner.write_starter(item)
    challenge_runner.open_in_editor(path)
    w, h    = screen.get_size()
    font    = _font(24)
    big     = _font(34)
    code    = pygame.font.SysFont("consolas,courier", 20)
    hints   = 0
    passed  = False
    result  = None

    while True:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return
                if e.key == pygame.K_h and hints < len(item["hints"]):
                    hints += 1
                if e.key == pygame.K_r and not passed:
                    passed, result = challenge_runner.run(item)
                    if passed:
                        progress_tracker.log_event("python", item["cluster"], item["id"],
                                                   "challenge_done")
                        character.set_expression("celebrating")
                    else:
                        character.set_expression("patient")
                if e.key == pygame.K_RETURN and passed:
                    return
        character.update(1 / 60)

        screen.fill(BG)
        character.pos = (int(w * 0.17), int(h * 0.93))
        character.draw(screen)
        x, y, col = int(w * 0.38), 56, int(w * 0.56)
        kind = "project" if item["kind"] == "project" else "challenge"
        screen.blit(big.render(f"{kind}: {item['title']}", True, INK), (x, y)); y += 50
        for ln in _wrap(font, item["prompt"], col):
            screen.blit(font.render(ln, True, INK), (x, y)); y += font.get_linesize()
        y += 12
        screen.blit(font.render("your file (open it, solve it, save):", True, SOFT), (x, y)); y += 28
        screen.blit(code.render(os.path.relpath(path), True, (190, 214, 200)), (x, y)); y += 40
        for i in range(hints):
            for ln in _wrap(font, "hint: " + item["hints"][i], col):
                screen.blit(font.render(ln, True, (168, 180, 156)), (x, y)); y += font.get_linesize()
        if result is not None:
            y += 12
            said = (random.choice(voice.get("correct", ["Yes. There it is."])) if passed
                    else random.choice(voice.get("incorrect", ["Not yet. Look again."])))
            for ln in _wrap(font, said, col):
                screen.blit(font.render(ln, True, (150, 200, 160) if passed else (212, 190, 168)),
                            (x, y)); y += font.get_linesize()
            for ln in _wrap(code, result, col):
                screen.blit(code.render(ln, True, (150, 160, 172)), (x, y)); y += 24
        footer = ("passed - enter to return to the sky" if passed
                  else "r to run   h for a hint   esc to step away")
        screen.blit(font.render(footer, True, SOFT), (x, h - 44))
        pygame.display.flip()


def _converse(screen, clock, character):
    # the shared conversation loop (talk and the daily check-in both use it).
    # nothing typed is stored. returns the Conversation on leaving, so the
    # check-in can read the day's mood from it.
    from core import companion
    w, h  = screen.get_size()
    font  = _font(24)
    small = _font(20)
    conv  = companion.Conversation()      # holds the thread for this whole sitting
    turns = [("her", conv.open())]
    character.set_expression("neutral")

    while True:
        said = _ask_line(screen, clock, "say anything, or start with ? to look something up. esc to leave")
        if said is None:
            conv.end()      # she keeps what's worth keeping; the words still go
            return conv
        turns.append(("you", said))
        if said.startswith("?"):
            # a question to look up. only when the mirror-self layer is on (your own
            # key); grounded and never made up - if she can't verify it, she says so.
            import echoself_core
            q = said[1:].strip()
            if not q:
                answer = "ask me something after the ?, and i'll look it up."
            elif not echoself_core.llm_available():
                answer = ("i can look things up only when the mirror-self layer is on - your "
                          "own key. without it i can't promise the answer's real, so i won't guess.")
            else:
                try:
                    answer = echoself_core.research(q)
                except Exception:
                    answer = ("i tried to look that up but couldn't reach an answer i trust. "
                              "better to give you nothing than something made up.")
            character.set_expression("thinking")
            turns.append(("her", answer))
        else:
            r = conv.say(said)
            companion.log_emotion(r["emotion"], r["intensity"])
            # the conversation trains the personality: a little drift per exchange
            if not r["crisis"]:
                from character import personality_drift
                d = personality_drift.load()
                personality_drift.nudge_emotion(d, r["emotion"])
                personality_drift.save(d)
            character.set_expression(companion.EXPRESSION.get(r["emotion"], "neutral"))
            turns.append(("her", r["reply"]))

        showing = True
        while showing:
            dt = clock.tick(60) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    conv.end()
                    return conv
                if e.type == pygame.KEYDOWN:
                    showing = False
            character.update(dt)
            screen.fill(BG)
            character.pos = (int(w * 0.17), int(h * 0.96))
            character.draw(screen)
            x, col = int(w * 0.36), int(w * 0.58)
            blocks = []
            for who, text in turns[-6:]:
                color = WARM if who == "her" else INK
                for i, ln in enumerate(_wrap(font, text, col)):
                    blocks.append((("-  " if i == 0 else "   ") + ln, color))
            y = max(60, h - 110 - len(blocks) * font.get_linesize())
            for text, color in blocks:
                screen.blit(font.render(text, True, color), (x, y))
                y += font.get_linesize()
            screen.blit(small.render("press a key to keep talking - esc to leave", True, SOFT),
                        (x, h - 44))
            pygame.display.flip()


def talk(screen, clock, character):
    # the `t` key: just a conversation, whenever you want one
    _converse(screen, clock, character)


def daily_checkin(screen, clock, character, profile):
    # the once-a-day check-in on launch. it's the same conversation - she opens
    # with how your day was - but when you step away she reads the day's mood from
    # what you said and logs it, so the brain still gets its number without a form.
    from core import daily
    conv = _converse(screen, clock, character)
    daily.log_checkin(conv, profile)


_HELP_WORLDS = [
    ("the ambient world", "where you are now. a sky, the character, and quiet. just be here, or reach for anything below."),
    ("the learning world", "press tab. the character teaches you to code - python deep, with c, c++ and java to try."),
    ("drift", "press d. the softest place: no lessons, no numbers, no demands. for the heavy days."),
]

_HELP_KEYS = [
    ("tab", "learn - the lessons"),
    ("t", "talk - she listens, and reads how you feel (start a line with ? to look something up)"),
    ("g", "your progress - how far you've come, and where you switch language"),
    ("p", "what she remembers about you"),
    ("e", "how far - your echo distance"),
    ("c", "a coding challenge in your own editor"),
    ("b", "remake your character"),
    ("l", "letters    v  the vault (private, encrypted)"),
    ("s", "settings    d  drift    m  mute    esc  leave"),
]


def show_help(screen, clock):
    # the one thing a first-timer needs: what this place is, and what the keys do.
    # shown once after session zero, and any time on 'h'. presence over pressure -
    # nothing here is a task list, it's an invitation.
    w, h   = screen.get_size()
    title  = _font(38)
    head   = _font(26)
    font   = _font(23)
    soft   = _font(20)
    while True:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_q, pygame.K_h):
                    return
        screen.fill(BG)
        screen.blit(title.render("EchoSelf - how this place works", True, INK), (60, 40))
        y = 104
        for name, what in _HELP_WORLDS:
            screen.blit(head.render(name, True, WARM), (60, y))
            for ln in _wrap(font, what, w - 120):
                y += 28
                screen.blit(font.render(ln, True, (200, 208, 220)), (60, y))
            y += 42
        y += 6
        screen.blit(head.render("the keys", True, WARM), (60, y))
        y += 36
        for key, what in _HELP_KEYS:
            screen.blit(font.render(key, True, (224, 214, 180)), (60, y))
            screen.blit(font.render(what, True, (196, 204, 216)), (140, y))
            y += 30
        screen.blit(soft.render("she learns you quietly. there's no wrong way to be here.   -   esc to close",
                                True, SOFT), (60, h - 44))
        pygame.display.flip()


def show_mastery(screen, clock, character):
    # how far you've come - the don't-give-up dashboard. per-topic progress, the
    # single next step, momentum without guilt, a welcome back if you've been away.
    import echoself_core
    w, h    = screen.get_size()
    title   = _font(38)
    font    = _font(26)
    soft    = _font(20)
    big     = _font(30)
    accent  = character.spec.palette[0]
    tracks  = echoself_core.learning_tracks()
    report  = echoself_core.mastery_report()
    while True:
        dt = clock.tick(60) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_q):
                    return
                if pygame.K_1 <= e.key <= pygame.K_4:        # switch language
                    i = e.key - pygame.K_1
                    if i < len(tracks):
                        echoself_core.set_learning_track(tracks[i][0])
                        report = echoself_core.mastery_report()
        character.update(dt)
        screen.fill(BG)
        character.pos = (int(w * 0.84), int(h * 1.02))
        character.draw(screen)

        screen.blit(title.render("how far you've come", True, INK), (60, 44))
        # which language, and how to switch
        switch = "   ".join(f"{i + 1} {name}" + (" <-" if tr == report["track"] else "")
                            for i, (tr, name) in enumerate(tracks))
        screen.blit(soft.render(switch, True, SOFT), (60, 92))
        y = 132
        # the topic bars
        bar_w = int(w * 0.46)
        for c in report["clusters"]:
            screen.blit(font.render(c["title"], True, INK), (60, y))
            screen.blit(soft.render(f"{c['done']}/{c['total']}", True, SOFT),
                        (60 + bar_w + 16, y + 2))
            track = pygame.Rect(60, y + 30, bar_w, 12)
            pygame.draw.rect(screen, (40, 46, 58), track, border_radius=6)
            fill = pygame.Rect(60, y + 30, int(bar_w * c["mastery"]), 12)
            pygame.draw.rect(screen, accent, fill, border_radius=6)
            y += 64

        # the overall, a little brighter
        y += 8
        screen.blit(big.render(f"{int(report['overall'] * 100)}% of the way", True, WARM),
                    (60, y))
        y += 56

        # the one next step, and the closer-than-it-feels line
        screen.blit(font.render(report["next_line"], True, (206, 214, 224)), (60, y))
        y += 40
        screen.blit(soft.render(report["momentum"], True, SOFT), (60, y))
        if report["welcome_back"]:
            y += 30
            for ln in _wrap(soft, report["welcome_back"], int(w * 0.7)):
                screen.blit(soft.render(ln, True, (186, 200, 178)), (60, y))
                y += soft.get_linesize()

        screen.blit(soft.render("1-4 switch language  -  tab to learn  -  esc to close",
                                True, SOFT), (60, h - 44))
        pygame.display.flip()


def settings_screen(screen, clock):
    # the few choices that are the user's to make: whether she reaches out, and
    # whether her check-in stays general or leans on what she remembers.
    from core import settings
    w, h   = screen.get_size()
    title  = _font(38)
    font   = _font(28)
    soft   = _font(20)
    while True:
        s = settings.load()
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_q):
                    return
                if e.key == pygame.K_1:
                    settings.toggle_outreach()
                elif e.key == pygame.K_2:
                    settings.toggle_style()
        on    = s["outreach"]
        style = s["outreach_style"]
        screen.fill(BG)
        screen.blit(title.render("settings", True, INK), (60, 48))
        rows = [
            ("1.  she reaches out:  " + ("on" if on else "off"),
             "a gentle check-in once a day, only when you haven't come by."),
            ("2.  her check-in:  " + ("proactive" if style == "personal" else "general"),
             "general asks how your day was; proactive leans on what she remembers."),
        ]
        y = 140
        for line, note in rows:
            screen.blit(font.render(line, True, WARM), (60, y))
            screen.blit(soft.render(note, True, SOFT), (60, y + 36))
            y += 96
        screen.blit(soft.render("press a number to change it   -   esc to close", True, SOFT),
                    (60, h - 44))
        pygame.display.flip()


_KIND_LABEL = {"weight": "weighs on you", "lift": "lifts you", "person": "someone",
               "goal": "reaching for", "pattern": "a pattern", "note": "noted"}


def show_portrait(screen, clock):
    # what she remembers about you. everything she's gathered is here, in plain
    # words, and any line can be removed with a keypress - model A, made literal.
    # nothing is hidden, nothing ever left the machine.
    import echoself_core
    w, h    = screen.get_size()
    title   = _font(38)
    font    = _font(26)
    soft    = _font(20)
    label   = _font(18)
    while True:
        items = echoself_core.portrait_facts(9)   # the strongest nine; number keys remove
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_q):
                    return
                if pygame.K_1 <= e.key <= pygame.K_9:
                    i = e.key - pygame.K_1
                    if i < len(items):
                        echoself_core.forget_fact(items[i]["id"])
        screen.fill(BG)
        screen.blit(title.render("what she remembers about you", True, INK), (60, 44))
        screen.blit(soft.render("everything she's kept is here. nothing left this machine.",
                                True, SOFT), (60, 92))
        y = 150
        if not items:
            screen.blit(font.render("she hasn't gathered anything yet.", True, INK), (60, y))
            screen.blit(soft.render("she will, the more you talk. it stays here, with you.",
                                    True, SOFT), (60, y + 36))
        else:
            for i, f in enumerate(items):
                tag = _KIND_LABEL.get(f.get("kind"), "noted")
                screen.blit(font.render(f"{i + 1}.  {f['text']}", True, WARM), (60, y))
                screen.blit(label.render(tag, True, SOFT), (w - 220, y + 4))
                y += font.get_linesize() + 14
        screen.blit(soft.render("press a number to forget that line   -   esc to close",
                                True, SOFT), (60, h - 44))
        pygame.display.flip()


def safety_plan_screen(screen, clock):
    # your plan for the hard moments, written when you're okay. build it a line at
    # a time; it's only ever yours - never shared, never sent. the crisis lines
    # for your region sit underneath it automatically.
    from core import safety_plan
    w, h  = screen.get_size()
    title = _font(36)
    font  = _font(24)
    soft  = _font(20)
    while True:
        plan = safety_plan.load()
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    return
                if pygame.K_1 <= e.key <= pygame.K_4:
                    idx = e.key - pygame.K_1
                    if idx < len(safety_plan.SECTIONS):
                        key, prompt = safety_plan.SECTIONS[idx]
                        line = _ask_line(screen, clock, prompt + ":")
                        if line:
                            safety_plan.add(key, line)
        screen.fill(BG)
        screen.blit(title.render("your safety plan", True, INK), (60, 40))
        screen.blit(soft.render("for the hard moments. only yours - never shared, never sent.",
                                True, SOFT), (60, 84))
        y = 140
        for i, (key, prompt) in enumerate(safety_plan.SECTIONS):
            screen.blit(font.render(f"{i + 1}.  {prompt}", True, WARM), (60, y))
            y += font.get_linesize() + 4
            for item in plan.get(key, []):
                screen.blit(soft.render(f"      - {item}", True, INK), (90, y))
                y += soft.get_linesize() + 2
            y += 14
        screen.blit(soft.render("press 1-4 to add a line   -   esc to close", True, SOFT),
                    (60, h - 44))
        pygame.display.flip()


def open_vault(screen, clock):
    # the encrypted private writing space. the system holds it; it never reads it.
    from core import vault
    new    = not vault.exists()
    prompt = "set a passphrase for your vault:" if new else "your vault passphrase:"
    passphrase = _ask_line(screen, clock, prompt, masked=True)
    if passphrase is None:
        return
    try:
        if new:
            vault.create(passphrase)
        entries = vault.unlock(passphrase)
    except vault.BadPassphrase:
        _flash(screen, clock, "that didn't open it. (the system can't either - that's the point.)")
        return

    while True:
        recent = entries[-6:]
        body   = ("Your vault. Nothing here is ever read by the system.\n\n" +
                  ("\n\n".join(f"{e['date']}\n{e['text']}" for e in recent)
                   if recent else "(empty - the first words can go here)"))
        # show, then offer to write
        _scroll_text(screen, clock, "The Vault", body +
                     "\n\n\npress enter to write a new line, esc to close")
        line = _ask_line(screen, clock, "write, just for you:")
        if line is None:
            return
        entries = vault.add_entry(passphrase, line)
