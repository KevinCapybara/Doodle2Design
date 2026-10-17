from backend.image_db import ImageDB
from backend.selection import plan_pairs, validate_pairs
from PIL import Image
import pytest
from scripts.build_manifest import build_manifest
from scripts.fetch_sample_images import CATEGORIES, make_image


def test_comparisons_never_repeat_actual_image_content():
    db = ImageDB()
    for seed in range(20):
        seen = set()
        for pair in plan_pairs(db, [], str(seed)):
            for image_id in (pair.left_id, pair.right_id):
                with Image.open(db.path(image_id)) as image:
                    pixels = image.convert("RGB").tobytes()
                assert pixels not in seen, f"Repeated image content: {image_id}, seed {seed}"
                seen.add(pixels)


def test_generated_patterns_are_visually_distinct():
    pixels = [make_image("patterns", index)[0].tobytes() for index in range(25)]
    assert len(set(pixels)) == 25


def test_library_filters_duplicate_pixels_under_different_ids(tmp_path):
    for category_index, category in enumerate(CATEGORIES):
        folder = tmp_path / "images/library" / category
        folder.mkdir(parents=True)
        for index in range(6):
            Image.new("RGB", (16, 16), (index*35, category_index*50, 80)).save(folder / f"{index}.png")
        # Same visual content in a differently sized and named file.
        Image.new("RGB", (64, 64), (0, category_index*50, 80)).save(folder / "z-copy.png")
    entries = build_manifest(tmp_path)
    db = ImageDB(tmp_path)
    assert len(db.images) == 24
    assert all(len(db.category(category)) == 6 for category in CATEGORIES)
    excluded = next(entry for entry in entries if entry["category"] == "architecture" and entry["path"].endswith("z-copy.png"))
    raw = [pair.model_dump() for pair in plan_pairs(db, [], "duplicates")]
    raw[0]["left_id"] = excluded["id"]
    assert validate_pairs(db, raw, []) is None


def test_library_requires_six_distinct_images_per_category(tmp_path):
    for category_index, category in enumerate(CATEGORIES):
        folder = tmp_path / "images/library" / category
        folder.mkdir(parents=True)
        for index in range(6):
            Image.new("RGB", (16, 16), (0, category_index*50, 80)).save(folder / f"{index}.png")
    build_manifest(tmp_path)
    with pytest.raises(ValueError, match="distinct"):
        ImageDB(tmp_path)


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
