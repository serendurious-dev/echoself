"""Echo Exchange - anonymous community sentences, surfaced as Echo Moments.

people contribute one sentence each: something their ideal self told them that
helped. they arrive by pull request into exchange/sentences.json (CC BY 4.0,
see CONTRIBUTING.md), anonymous by design. now and then one drifts quietly
across the ambient sky - a stranger's line, held out to whoever needs it
tonight.

the engine only reads the content here; contributions happen through git, not
the app, which is why this reader lives in core/ (MIT) while the sentences live
in exchange/ (CC BY 4.0).
"""

import os
import json
import random

EXCHANGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exchange")
_PATH        = os.path.join(EXCHANGE_DIR, "sentences.json")


def all_sentences():
    try:
        with open(_PATH, encoding="utf-8") as f:
            return list(json.load(f).get("sentences", []))
    except (OSError, ValueError):
        return []


def random_sentence():
    pool = all_sentences()
    return random.choice(pool) if pool else None
