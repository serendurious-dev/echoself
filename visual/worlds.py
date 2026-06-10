"""the three worlds, in pygame.

Ambient: the living sky. the character's color bleeds into the environment, stars
drift with the Echo Distance. Drift Mode lives here - soft sky, zero UI, the
character just sits and breathes.

Learning: the glowing lesson panel beside the character, ambient particles, the
world's color shifting with the detected state.

transitions are fades, never hard cuts. the character is present in every world.

right now the worlds are placeholder skies - the real sky is issue #3, the
character is issue #2. this file owns the base class, the manager and the fades.
"""

import pygame

FPS          = 60
WINDOW_SIZE  = (1280, 720)
FADE_SECONDS = 0.7   # full out-and-in. long enough to feel soft, short enough to not annoy


def vgradient(size, top, bottom):
    # paint a 1x2 column and let smoothscale do the blending. cheap and looks fine.
    column = pygame.Surface((1, 2))
    column.set_at((0, 0), top)
    column.set_at((0, 1), bottom)
    return pygame.transform.smoothscale(column, size)


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


class PlaceholderWorld(World):
    # a quiet gradient and a small caption, honest about being a placeholder.
    # each world gets its own palette so the fades have something to fade between.

    def __init__(self, size, name, top, bottom, caption):
        super().__init__(size)
        self.name    = name
        self.caption = caption
        self.sky     = vgradient(size, top, bottom)
        self.font    = pygame.font.Font(None, 24)
        self.pulse   = 0.0

    def update(self, dt):
        self.pulse += dt

    def draw(self, surface):
        surface.blit(self.sky, (0, 0))
        # caption breathes a little so the screen never feels frozen
        import math
        alpha = int(90 + 40 * math.sin(self.pulse * 1.6))
        text  = self.font.render(self.caption, True, (235, 235, 235))
        text.set_alpha(alpha)
        surface.blit(text, (24, self.size[1] - 40))


def default_worlds(size):
    return {
        "ambient":  PlaceholderWorld(size, "ambient", (18, 24, 44), (64, 54, 96),
                                     "ambient world  -  1 learning, d drift, esc quit"),
        "learning": PlaceholderWorld(size, "learning", (14, 32, 38), (38, 84, 92),
                                     "learning world  -  2 ambient, d drift, esc quit"),
        "drift":    PlaceholderWorld(size, "drift", (10, 12, 24), (30, 36, 58),
                                     "drift mode  -  d to come back"),
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
    # teleports an animation.
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("EchoSelf")
    clock  = pygame.time.Clock()
    worlds = WorldManager(WINDOW_SIZE)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_1:
                    worlds.switch("ambient")
                elif event.key == pygame.K_2:
                    worlds.switch("learning")
                elif event.key == pygame.K_d:
                    worlds.toggle_drift()
                else:
                    worlds.handle(event)
            else:
                worlds.handle(event)
        worlds.update(dt)
        worlds.draw(screen)
        pygame.display.flip()

    pygame.quit()
    return 0
