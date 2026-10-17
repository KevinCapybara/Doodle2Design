"""Optional vision providers share the same validated taste-analysis pipeline."""
import asyncio
import base64
import json
import logging
import os
import time

from anthropic import AsyncAnthropic

from backend import ai_provider, mock, prompts
from backend.imaging import fix_contrast, prepare_image
from backend.schemas import BaselineProfile, VibeTokens, Visuals
from backend.selection import category_order, plan_pairs, validate_pairs

logger = logging.getLogger("doodle2design.vlm")


def mock_mode():
    return not ai_provider.available()


def image_block(data):
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(prepare_image(data)).decode("ascii")}}


def parse_json(value):
    value = value.strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(value)


async def request_json(system, content, validator):
    """At most two attempts total, including malformed JSON/schema failures."""
    if ai_provider.provider_name() == "openai":
        return await ai_provider.request_openai(system, content, validator, model=ai_provider.model_name("vision"))
    async with AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=30.0, max_retries=0) as client:
        for attempt in range(2):
            started = time.perf_counter()
            try:
                message = await asyncio.wait_for(client.messages.create(model=ai_provider.model_name("vision"), max_tokens=2200, temperature=0, system=system, messages=[{"role": "user", "content": content}]), timeout=30)
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
        def reference(image_id):
            entry = db.images[image_id]
            return {"id": image_id, "filename": db.path(image_id).stem, "tags": entry["tags"],
                    "observed": entry.get("observed", {}), "feeling": entry.get("feeling", {}),
                    "suggested_design": entry.get("suggested_design", {})}
        losers = [reference(c.loser_id) for c in session.choices]
        winners_metadata = [reference(c.winner_id) for c in session.choices]
        text = prompts.EXTRACTION_USER+"\nBaseline: "+session.baseline.model_dump_json()+"\nSelected reference annotations (AI interpretations, not ground truth): "+json.dumps(winners_metadata)+"\nRejected references: "+json.dumps(losers)
        content = [image_block(i) for i in session.images + winners] + [{"type": "text", "text": text}]
        # The tighter overall deadline keeps the on-stage extraction transition bounded.
        result = await asyncio.wait_for(request_json(prompts.EXTRACTION_SYSTEM, content, validate_extraction), timeout=14)
        return fix_contrast(result), False
    except Exception:
        logger.warning("Using offline theme after model error or extraction deadline")
        return fallback, True


def validate_extraction(data):
    """New inference must be complete; old saved token files can still use defaults."""
    visuals = data.get("visuals") if isinstance(data, dict) else None
    if not isinstance(visuals, dict) or not set(Visuals.model_fields).issubset(visuals):
        raise ValueError("Extraction must include the complete visuals group.")
    return VibeTokens.model_validate(data)
