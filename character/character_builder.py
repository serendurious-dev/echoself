"""packs in, specs out - presets plus the user's Session Zero choices."""

import os
import json

from character.renderer import CharacterSpec, PACK_DIR, Character, hex_to_rgb
from character import art_pack

PACK_IDS = ["gentle_guide", "strict_mentor", "playful_rival",
            "philosophical_elder", "quiet_empath"]

# the quick dials Session Zero offers on the preset path - small on purpose,
# enough to make a ready-made character yours without stalling at a menu.
BUILDS      = ["female", "male"]
HAIR_STYLES = ["long", "short", "fluffy", "spiky"]
SKIN_TONES  = ["#F7E0CC", "#F2D5C0", "#D9A878", "#A8714A", "#6B4A35"]
# a palette is [light, accent, deep]. it colors the character's aura and the sky
# around them - your light - so it shows even when the body is painted art.
PALETTES = [
    ["#7FB5A8", "#E8DCC8", "#4A6670"],   # the gentle guide's own
    ["#9B8AC4", "#D8CCE8", "#4A4458"],   # violet dusk
    ["#E8A04C", "#F4D8A8", "#8A4A2E"],   # amber
    ["#A8C4D8", "#E8E4DC", "#5A6E7A"],   # cool blue
    ["#C77B8B", "#F0D8DC", "#5A3A44"],   # rose
    ["#7AA86A", "#DCE8C8", "#3E5238"],   # green
]

# the rest of the knobs, for the full "make your own" builder. these reach every
# parameter the procedural renderer already draws, so a from-scratch character is
# really yours - not a preset with a few sliders.
FORMS       = ["soft", "slender", "broad"]
HAIR_COLORS = ["#2B2622", "#4A3B33", "#6E5A4E", "#8A5A3C", "#A8714A", "#C9A063", "#E8D5A8"]
EYE_COLORS  = ["#4A2E22", "#6E4A2E", "#5B8A80", "#3E6E8A", "#5A6A4A", "#6E6E78", "#C0883E"]
OUTFITS     = [["#5E8C80", "#4A6E66"], ["#9B8AC4", "#5A4E78"], ["#C77B8B", "#7A4452"],
               ["#5A7A9A", "#3E5670"], ["#7AA86A", "#4E6E48"], ["#C9A063", "#8A6A3E"],
               ["#6A6E78", "#44484E"]]
SYMBOLS     = ["circle", "star", "spark", "lantern"]


def _as_rgb(c):
    return hex_to_rgb(c) if isinstance(c, str) else tuple(c)


def load_pack(pack_id):
    with open(os.path.join(PACK_DIR, pack_id + ".json"), encoding="utf-8") as f:
        return json.load(f)


def all_packs():
    return [load_pack(p) for p in PACK_IDS]


def spec_from_pack(pack, hair_style=None, skin=None, build=None, palette=None,
                   hair_color=None, eye_color=None, outfit=None, form=None, symbol=None):
    # a base look (a preset's, or the neutral default) with the user's choices
    # laid over it. every override is optional - only what was picked gets applied,
    # so the same function serves the quick preset dials and the full builder.
    spec = CharacterSpec.from_visual(pack.get("visual", {}))
    if hair_style:
        spec.hair_style = hair_style
    if skin:
        spec.skin = _as_rgb(skin)
    if build:
        spec.gender = build
    if palette:
        spec.palette = [_as_rgb(c) for c in palette]
    if hair_color:
        spec.hair_color = _as_rgb(hair_color)
    if eye_color:
        spec.eye_color = _as_rgb(eye_color)
    if outfit:
        spec.outfit = [_as_rgb(c) for c in outfit]
    if form:
        spec.form = form
    if symbol:
        spec.symbol = symbol
    return spec


def spec_from_profile(profile):
    # what default_worlds calls every launch. a preset character starts from its
    # pack; a "make your own" character (pack == "custom") starts from a neutral
    # base and is fully overridden by its saved knobs. broken or missing pieces
    # fall back to the gentle guide - the app never refuses to start.
    try:
        c       = profile["character"]
        pack_id = c.get("pack")
        base    = load_pack(pack_id if pack_id and pack_id != "custom" else "gentle_guide")
        return spec_from_pack(base,
                              hair_style=c.get("hair_style"),
                              skin=c.get("skin"),
                              build=c.get("build"),
                              palette=c.get("palette"),
                              hair_color=c.get("hair_color"),
                              eye_color=c.get("eye_color"),
                              outfit=c.get("outfit"),
                              form=c.get("form"),
                              symbol=c.get("symbol"))
    except (KeyError, TypeError, OSError, ValueError):
        return spec_from_pack(load_pack("gentle_guide"))


def make_character(spec, pos=(640, 540), height=300):
    # the factory the rest of the app calls. if the chosen character has a real
    # art pack on disk, you get the layered ArtCharacter; otherwise the
    # procedural figure. either one honors the same interface, so callers never
    # branch on it. a broken pack never crashes the app - it falls back.
    if art_pack.pack_dir(getattr(spec, "art", None)):
        try:
            return art_pack.ArtCharacter(spec, pos=pos, height=height)
        except (OSError, ValueError, KeyError):
            pass
    return Character(spec, pos=pos, height=height)


def voice_from_profile(profile):
    # the chosen personality's phrase banks, for live reactions. a custom-look
    # character carries its personality in a separate "voice" field (the look and
    # the voice are chosen apart); a preset's pack is its voice.
    try:
        c = profile["character"]
        return load_pack(c.get("voice") or c["pack"])["voice"]["phrases"]
    except (KeyError, TypeError, OSError, ValueError):
        return load_pack("gentle_guide")["voice"]["phrases"]
