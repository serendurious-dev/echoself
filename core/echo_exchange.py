"""Echo Exchange: anonymous community sentences, surfaced as Echo Moments."""

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
