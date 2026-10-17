"""Anthropic is optional at runtime: every inference has a deterministic fallback."""
import asyncio
import base64
import json
import logging
import os
import time

from anthropic import AsyncAnthropic

from backend import mock, prompts
from backend.imaging import fix_contrast, prepare_image
from backend.schemas import BaselineProfile, VibeTokens
from backend.selection import category_order, plan_pairs, validate_pairs

logger = logging.getLogger("doodle2design.vlm")


def mock_mode():
    return os.getenv("VIBE_MOCK") == "1" or not os.getenv("ANTHROPIC_API_KEY", "").strip()


def image_block(data):
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(prepare_image(data)).decode("ascii")}}


def parse_json(value):
    value = value.strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(value)


async def request_json(system, content, validator):
    """At most two attempts total, including malformed JSON/schema failures."""
    async with AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=30.0, max_retries=0) as client:
        for attempt in range(2):
            started = time.perf_counter()
            try:
                message = await asyncio.wait_for(client.messages.create(model=os.getenv("VLM_MODEL", "claude-sonnet-4-6"), max_tokens=2200, temperature=0, system=system, messages=[{"role": "user", "content": content}]), timeout=30)
                text = "".join(block.text for block in message.content if block.type == "text")
                return validator(parse_json(text))
            except asyncio.CancelledError:
                raise
            except Exception as error:
                # Never log request bodies, image data, or credentials.
                logger.warning("VLM attempt %d failed (%s)", attempt+1, type(error).__name__)
            finally:
                logger.info("VLM attempt %d latency %.2fs", attempt+1, time.perf_counter()-started)
    raise RuntimeError("Vision inference unavailable after retry")


async def analyze_baseline(images):
    if not mock_mode():
        try:
            content = [image_block(i) for i in images] + [{"type": "text", "text": prompts.BASELINE_USER}]
            return await request_json(prompts.BASELINE_SYSTEM, content, BaselineProfile.model_validate), False
        except Exception:
            logger.warning("Using offline baseline")
    return mock.baseline_profile(images), True


async def plan_comparisons(db, profile, seed):
    fallback = plan_pairs(db, profile.preferred_categories, seed)
    if mock_mode() or all(entry.get("tags") for entry in db.images.values()):
        return fallback, mock_mode()
    try:
        entries = [{"id": i["id"], "category": i["category"], "tags": i["tags"], "hint": db.path(i["id"]).stem} for i in db.images.values()]
        payload = {"baseline": profile.model_dump(), "category_order": category_order(profile.preferred_categories), "images": entries}
        def validate(raw):
            pairs = validate_pairs(db, raw.get("pairs"), profile.preferred_categories, seed)
            if not pairs:
                raise ValueError("Invalid comparison plan")
            return pairs
        pairs = await request_json(prompts.PLANNING_SYSTEM, [{"type": "text", "text": prompts.PLANNING_USER+"\n"+json.dumps(payload)}], validate)
        return pairs, False
    except Exception:
        logger.warning("Using seeded offline comparison plan")
        return fallback, True


async def extract_theme(session, db):
    winners = [prepare_image(db.path(c.winner_id).read_bytes()) for c in session.choices]
    # Input remains the anchor; selected references refine it. Rejections inform the real VLM.
    fallback = mock.extract_tokens(session.images*3 + winners, session.choices, db)
    if mock_mode():
        return fallback, True
    try:
        losers = [{"filename": db.path(c.loser_id).stem, "tags": db.images[c.loser_id]["tags"]} for c in session.choices]
        text = prompts.EXTRACTION_USER+"\nBaseline: "+session.baseline.model_dump_json()+"\nRejected references: "+json.dumps(losers)
        content = [image_block(i) for i in session.images + winners] + [{"type": "text", "text": text}]
        # The tighter overall deadline keeps the on-stage extraction transition bounded.
        result = await asyncio.wait_for(request_json(prompts.EXTRACTION_SYSTEM, content, VibeTokens.model_validate), timeout=14)
        return fix_contrast(result), False
    except Exception:
        logger.warning("Using offline theme after model error or extraction deadline")
        return fallback, True
