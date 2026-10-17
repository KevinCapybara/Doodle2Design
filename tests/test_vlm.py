import asyncio
from types import SimpleNamespace
import pytest

from backend import vlm
from backend.schemas import BaselineProfile
from io import BytesIO
from PIL import Image


def solid_png(color):
    stream = BytesIO()
    Image.new("RGB", (100, 100), color).save(stream, "PNG")
    return stream.getvalue()


def test_fences_are_removed():
    assert vlm.parse_json('```json\n{"ok": true}\n```') == {"ok": True}


def test_request_retries_invalid_json_once_then_validates(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-never-transmitted")
    answers = ["not json", '{"ok":true}']
    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] == 30 and kwargs["max_retries"] == 0
            self.messages = self
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def create(self, **kwargs): return SimpleNamespace(content=[SimpleNamespace(type="text", text=answers.pop(0))])
    monkeypatch.setattr(vlm, "AsyncAnthropic", FakeClient)
    assert asyncio.run(vlm.request_json("system", [], lambda value: value)) == {"ok": True}
    assert not answers


def test_baseline_failure_falls_back(monkeypatch):
    monkeypatch.setenv("VIBE_MOCK", "0")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-never-transmitted")
    async def fail(*args): raise RuntimeError("No network")
    monkeypatch.setattr(vlm, "request_json", fail)
    profile, degraded = asyncio.run(vlm.analyze_baseline([solid_png("#132133")]))
    assert isinstance(profile, BaselineProfile) and degraded


def test_image_block_is_normalized_jpeg():
    import base64
    from io import BytesIO
    from PIL import Image
    block = vlm.image_block(solid_png("#123456"))
    assert block["source"]["media_type"] == "image/jpeg"
    with Image.open(BytesIO(base64.b64decode(block["source"]["data"]))) as image:
        assert max(image.size) <= 768


def test_extraction_failure_returns_valid_degraded_theme(monkeypatch):
    from backend.image_db import ImageDB
    from backend.schemas import Choice, VibeTokens
    from backend.session import Session
    from backend.selection import plan_pairs
    from backend.mock import baseline_profile
    monkeypatch.setenv("VIBE_MOCK", "0")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-never-transmitted")
    async def fail(*args): raise TimeoutError("simulated deadline")
    monkeypatch.setattr(vlm, "request_json", fail)
    db = ImageDB()
    session = Session(id="fallback-test", images=[solid_png("#102030")])
    session.baseline = baseline_profile(session.images)
    for pair in plan_pairs(db, [], "fallback-test"):
        session.choices.append(Choice(round=pair.round, category=pair.category, winner_id=pair.left_id, loser_id=pair.right_id))
    tokens, degraded = asyncio.run(vlm.extract_theme(session, db))
    assert isinstance(tokens, VibeTokens) and degraded


def test_invalid_model_pairs_fall_back_to_valid_seeded_plan(monkeypatch):
    from backend.image_db import ImageDB
    from backend.mock import baseline_profile
    monkeypatch.setenv("VIBE_MOCK", "0")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-never-transmitted")
    async def invalid(system, content, validator):
        return validator({"pairs": [{"category": "bad", "left_id": "not-real", "right_id": "not-real"}]*10})
    monkeypatch.setattr(vlm, "request_json", invalid)
    db = ImageDB()
    for entry in db.images.values():
        entry["tags"] = []  # Exercise model planning; tagged photos intentionally skip it.
    pairs, degraded = asyncio.run(vlm.plan_comparisons(db, baseline_profile([solid_png("#cbdcba")]), "seed"))
    assert len(pairs) == 10 and degraded
    assert len({i for pair in pairs for i in (pair.left_id, pair.right_id)}) == 20


def test_new_model_extraction_requires_complete_visual_direction():
    from backend.mock import extract_tokens
    tokens = extract_tokens([solid_png("#5c8450")]).model_dump()
    assert vlm.validate_extraction(tokens).visuals.motif == "forest"
    tokens.pop("visuals")
    with pytest.raises(ValueError, match="visual"):
        vlm.validate_extraction(tokens)
    tokens["visuals"] = {"motif": "forest"}
    with pytest.raises(ValueError, match="visual"):
        vlm.validate_extraction(tokens)
