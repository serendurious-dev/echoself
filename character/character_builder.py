"""packs in, specs out - and the user's own touches on top.

the five preset personalities live in characters/ as JSON packs. this module
loads them, turns a pack into a renderable CharacterSpec, and applies the
choices the user made in Session Zero (hair, skin) over the preset. the pack
file itself is never modified - your character is the pack plus you.
"""

import os
import json

from character.renderer import CharacterSpec, PACK_DIR

PACK_IDS = ["gentle_guide", "strict_mentor", "playful_rival",
            "philosophical_elder", "quiet_empath"]

# the dials Session Zero offers. small on purpose - enough to make them yours,
# not enough to stall you at a menu on day one.
HAIR_STYLES = ["long", "short", "spiky"]
SKIN_TONES  = ["#F7E0CC", "#F2D5C0", "#D9A878", "#A8714A", "#6B4A35"]


def load_pack(pack_id):
    with open(os.path.join(PACK_DIR, pack_id + ".json"), encoding="utf-8") as f:
        return json.load(f)


def all_packs():
    return [load_pack(p) for p in PACK_IDS]


def spec_from_pack(pack, hair_style=None, skin=None):
    # the preset's look, with the user's choices laid over it
    spec = CharacterSpec.from_visual(pack.get("visual", {}))
    if hair_style:
        spec.hair_style = hair_style
    if skin:
        spec.skin = CharacterSpec.from_visual({"skin": skin}).skin
    return spec


def spec_from_profile(profile):
    # what default_worlds calls every launch. broken or missing pieces fall
    # back to the gentle guide, the app never refuses to start.
    try:
        c = profile["character"]
        return spec_from_pack(load_pack(c["pack"]),
                              hair_style=c.get("hair_style"),
                              skin=c.get("skin"))
    except (KeyError, TypeError, OSError, ValueError):
        return spec_from_pack(load_pack("gentle_guide"))


def voice_from_profile(profile):
    # the chosen personality's phrase banks, for live reactions
    try:
        return load_pack(profile["character"]["pack"])["voice"]["phrases"]
    except (KeyError, TypeError, OSError, ValueError):
        return load_pack("gentle_guide")["voice"]["phrases"]
