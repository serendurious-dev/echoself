"""the Echo Distance, drawn. matplotlib rendered onto pygame surfaces.

a four-axis radar (Mental, Behavioral, Emotional, Learning) showing the gap
between who you are and who you want to be, and a 30-day timeline of all four.
matplotlib runs on the Agg backend and the figure is blitted into pygame, so
this works headless too.

the charts plot closeness, not distance - the axis fills toward the edge as
the gap closes, because watching it grow is the point.
"""

import matplotlib
matplotlib.use("Agg")               # no window, render to a buffer
import matplotlib.pyplot as plt
import numpy as np
import pygame

from core import echo_distance

BG    = "#0E1422"
INK   = "#C8D0DC"
FAINT = "#3A4456"


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def _fig_to_surface(fig):
    fig.canvas.draw()
    size = fig.canvas.get_width_height()
    surf = pygame.image.frombuffer(bytes(fig.canvas.buffer_rgba()), size, "RGBA")
    plt.close(fig)
    return surf


def radar_surface(distances, accent=(127, 181, 168), px=440):
    # closeness = 1 - distance, so a closing gap reaches outward
    labels = ["Mental", "Behavioral", "Emotional", "Learning"]
    close  = [1.0 - distances[a] for a in echo_distance.AXES]
    ang    = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    close += close[:1]
    ang   += ang[:1]

    dpi = 100
    fig = plt.figure(figsize=(px / dpi, px / dpi), dpi=dpi)
    fig.patch.set_facecolor(BG)
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor(BG)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 1)
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels(labels, color=INK, fontsize=11)
    ax.set_yticks([0.25, 0.5, 0.75])
    ax.set_yticklabels([])
    ax.tick_params(colors=FAINT)
    for spine in ax.spines.values():
        spine.set_color(FAINT)
    ax.grid(color=FAINT, linewidth=0.6)
    col = _hex(accent)
    ax.plot(ang, close, color=col, linewidth=2)
    ax.fill(ang, close, color=col, alpha=0.30)
    fig.tight_layout(pad=0.6)
    return _fig_to_surface(fig)


def timeline_surface(rows, accent=(127, 181, 168), size=(760, 300)):
    dpi = 100
    fig = plt.figure(figsize=(size[0] / dpi, size[1] / dpi), dpi=dpi)
    fig.patch.set_facecolor(BG)
    ax = fig.add_subplot(111)
    ax.set_facecolor(BG)
    colors = {"mental": "#8AB0E0", "behavioral": "#E0B884",
              "emotional": "#D88AA8", "learning": _hex(accent)}
    if rows:
        xs = list(range(len(rows)))
        for axis in echo_distance.AXES:
            ax.plot(xs, [1.0 - r[axis] for r in rows], label=axis.title(),
                    color=colors[axis], linewidth=1.8)
        ax.set_xlim(0, max(1, len(rows) - 1))
    else:
        ax.text(0.5, 0.5, "the timeline fills in as the days do",
                color=FAINT, ha="center", va="center", transform=ax.transAxes)
    ax.set_ylim(0, 1)
    ax.set_title("Echo Distance, last 30 days (higher is closer)", color=INK, fontsize=11)
    ax.tick_params(colors=FAINT, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(FAINT)
    ax.grid(color=FAINT, linewidth=0.4, alpha=0.5)
    leg = ax.legend(loc="lower right", fontsize=8, facecolor=BG, edgecolor=FAINT)
    for text in leg.get_texts():
        text.set_color(INK)
    fig.tight_layout(pad=0.6)
    return _fig_to_surface(fig)


def show_echo_distance(screen, clock, profile, accent=(127, 181, 168)):
    # a quiet full-screen view: the radar, the timeline, and the mirror report
    # if the week has earned one. any key returns to the sky.
    from core import narrative_engine
    w, h   = screen.get_size()
    dist   = echo_distance.compute(profile)
    radar  = radar_surface(dist, accent, px=min(440, h // 2))
    line   = timeline_surface(echo_distance.history(30), accent,
                              size=(min(760, w - 80), 280))
    report = narrative_engine.mirror_report(profile)
    sky    = pygame.Surface((w, h))
    sky.fill((10, 14, 28))
    font   = pygame.font.Font(None, 24)
    title  = pygame.font.Font(None, 34)

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                running = False
        screen.blit(sky, (0, 0))
        screen.blit(title.render("how far, and how far you've come", True, INK), (40, 28))
        screen.blit(radar, (40, 80))
        screen.blit(line, (40 + radar.get_width() + 30, 80))
        ry = 80 + line.get_height() + 24
        for i, ln in enumerate(report.split("\n")):
            screen.blit(font.render(ln, True, (188, 196, 208)),
                        (40 + radar.get_width() + 30, ry + i * 26))
        screen.blit(font.render("any key - back to the sky", True, FAINT), (40, h - 40))
        pygame.display.flip()
