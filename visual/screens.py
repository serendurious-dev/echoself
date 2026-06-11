"""small full-screen views that pause the worlds: the Letters, the Vault.

these are quiet, text-only places. they take over the screen, do one calm
thing, and hand control back. the Vault screen is the one that touches the
encrypted diary - and even here, nothing is decrypted until the user types the
passphrase that only they know.
"""

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
        shown  = ("•" * len(typed)) if masked else typed
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
