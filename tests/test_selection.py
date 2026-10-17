from backend.image_db import ImageDB
from backend.selection import plan_pairs, validate_pairs


def test_pair_contract():
    db = ImageDB()
    pairs = plan_pairs(db, ["patterns", "landscapes"], "test-seed")
    assert len(pairs) == 10
    assert pairs[0].category == "patterns"
    assert [p.round for p in pairs] == list(range(1, 11))
    ids = [i for p in pairs for i in (p.left_id, p.right_id)]
    assert len(set(ids)) == 20
    for pair in pairs:
        assert db.images[pair.left_id]["category"] == db.images[pair.right_id]["category"] == pair.category
    assert {p.category for p in pairs} == {"architecture", "landscapes", "textures", "patterns"}
    assert all(sum(p.category == c for p in pairs) >= 2 for c in {p.category for p in pairs})
    assert pairs == plan_pairs(db, ["patterns", "landscapes"], "test-seed")


def test_invalid_model_plan_is_rejected():
    db = ImageDB()
    pairs = plan_pairs(db, [], "test-seed")
    raw = [p.model_dump() for p in pairs]
    raw[1]["left_id"] = raw[0]["left_id"]
    assert validate_pairs(db, raw, []) is None
