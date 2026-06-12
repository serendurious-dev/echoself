"""procedural ambient soundscape: a numpy drone that warms as the Echo Distance closes."""

import numpy as np

RATE        = 22050
SECONDS     = 16.0          # one slow breath; loops seamlessly
_BASE_HZ    = 110.0         # a low A
_BREATH_HZ  = 1.0 / SECONDS


def generate_tone(closeness, seconds=SECONDS, rate=RATE):
    # closeness 0..1 -> a stereo int16 buffer. fuller and louder as it rises.
    closeness = max(0.0, min(1.0, closeness))
    t = np.linspace(0, seconds, int(seconds * rate), endpoint=False)

    # harmonics: the upper ones come in as the gap closes, so it warms up
    partials = [(1.0, 0.50),
                (2.0, 0.18 + 0.18 * closeness),
                (3.0, 0.10 * closeness),
                (4.0, 0.06 * closeness)]
    wave = sum(amp * np.sin(2 * np.pi * _BASE_HZ * mult * t) for mult, amp in partials)

    # a slow breath in the amplitude, and a faint fifth for warmth when close
    breath = 0.62 + 0.38 * np.sin(2 * np.pi * _BREATH_HZ * t)
    wave  += 0.12 * closeness * np.sin(2 * np.pi * _BASE_HZ * 1.5 * t)
    wave  *= breath
    wave  *= 0.22 + 0.40 * closeness          # overall volume grows with closeness

    wave  = np.clip(wave, -1.0, 1.0)
    mono  = np.int16(wave * 32767 * 0.6)
    return np.column_stack([mono, mono])


class Soundscape:
    # owns the looping sound. set_closeness rebuilds it only when the mood
    # shifts enough to matter, so it is not regenerating every frame.

    def __init__(self):
        self._ok      = False
        self._sound   = None
        self._bucket  = None
        self._muted   = False

    def start(self):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=RATE, size=-16, channels=2)
            self._ok = True
        except Exception:
            self._ok = False          # no audio device - stay silent
        return self._ok

    def set_closeness(self, closeness):
        if not self._ok or self._muted:
            return
        bucket = round(max(0.0, min(1.0, closeness)) * 4) / 4   # 0, .25, .5, .75, 1
        if bucket == self._bucket:
            return
        self._bucket = bucket
        try:
            import pygame
            self._sound = pygame.sndarray.make_sound(generate_tone(bucket))
            self._sound.set_volume(0.5)
            self._sound.play(loops=-1, fade_ms=1500)
        except Exception:
            self._ok = False

    def toggle_mute(self):
        self._muted = not self._muted
        try:
            import pygame
            if self._muted:
                pygame.mixer.fadeout(800)
            else:
                self._bucket = None        # force a rebuild on next set_closeness
        except Exception:
            pass
        return self._muted

    def stop(self):
        try:
            import pygame
            pygame.mixer.fadeout(800)
        except Exception:
            pass
