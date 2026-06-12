"""packs in, specs out - presets plus the user's Session Zero choices."""

import os
import json

from character.renderer import CharacterSpec, PACK_DIR, Character
from character import art_pack

PACK_IDS = ["gentle_guide", "strict_mentor", "playful_rival",
            "philosophical_elder", "quiet_empath"]

# the dials Session Zero offers. small on purpose - enough to make them yours,
# not enough to stall you at a menu on day one.
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


def load_pack(pack_id):
    with open(os.path.join(PACK_DIR, pack_id + ".json"), encoding="utf-8") as f:
        return json.load(f)


def all_packs():
    return [load_pack(p) for p in PACK_IDS]


def spec_from_pack(pack, hair_style=None, skin=None, build=None, palette=None):
    # the preset's look, with the user's choices laid over it
    spec = CharacterSpec.from_visual(pack.get("visual", {}))
    if hair_style:
        spec.hair_style = hair_style
    if skin:
        spec.skin = CharacterSpec.from_visual({"skin": skin}).skin
    if build:
        spec.gender = build
    if palette:
        spec.palette = CharacterSpec.from_visual({"palette": palette}).palette
    return spec


def spec_from_profile(profile):
    # what default_worlds calls every launch. broken or missing pieces fall
    # back to the gentle guide, the app never refuses to start.
    try:
        c = profile["character"]
        return spec_from_pack(load_pack(c["pack"]),
                              hair_style=c.get("hair_style"),
                              skin=c.get("skin"),
                              build=c.get("build"),
                              palette=c.get("palette"))
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
    # the chosen personality's phrase banks, for live reactions
    try:
        return load_pack(profile["character"]["pack"])["voice"]["phrases"]
    except (KeyError, TypeError, OSError, ValueError):
        return load_pack("gentle_guide")["voice"]["phrases"]
