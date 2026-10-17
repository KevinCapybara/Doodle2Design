"""Cached ten-round plans, with deterministic same-category fallback."""
import random
from backend.image_db import CATEGORIES
from backend.schemas import ABPair


def category_order(preferred):
    order = list(dict.fromkeys([*preferred, *CATEGORIES]))
    return [order[i % 4] for i in range(10)]


def plan_pairs(db, preferred, seed):
    rng = random.Random(seed)
    used, pairs = set(), []
    for number, category in enumerate(category_order(preferred), 1):
        available = [i for i in db.category(category) if i["id"] not in used]
        rng.shuffle(available)
        tagged = [i for i in available if i.get("tags")]
        if len(tagged) > 1:
            a, b = min(((a, b) for n, a in enumerate(tagged) for b in tagged[n+1:]), key=lambda pair: len(set(pair[0]["tags"]) & set(pair[1]["tags"])))
        else:
            a, b = available[:2]
        if rng.random() > .5:
            a, b = b, a
        used.update((a["id"], b["id"]))
        pairs.append(ABPair(round=number, category=category, left_id=a["id"], right_id=b["id"], left_url=db.url(a["id"]), right_url=db.url(b["id"])))
    return pairs


def validate_pairs(db, raw, preferred, seed="model-plan"):
    if not isinstance(raw, list) or len(raw) != 10:
        return None
    used, pairs = set(), []
    rng = random.Random(seed)
    for number, (pair, expected) in enumerate(zip(raw, category_order(preferred)), 1):
        if not isinstance(pair, dict):
            return None
        a, b = pair.get("left_id"), pair.get("right_id")
        if not isinstance(a, str) or not isinstance(b, str) or a not in db.images or b not in db.images or a == b or a in used or b in used:
            return None
        if pair.get("category") != expected or db.images[a]["category"] != expected or db.images[b]["category"] != expected:
            return None
        used.update((a, b))
        if rng.random() > .5:
            a, b = b, a
        pairs.append(ABPair(round=number, category=expected, left_id=a, right_id=b, left_url=db.url(a), right_url=db.url(b)))
    return pairs
