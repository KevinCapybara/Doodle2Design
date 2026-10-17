"""Provider selection and the OpenAI Responses API boundary."""
import asyncio
import json
import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger("doodle2design.ai")
DEFAULT_OPENAI_MODEL = "gpt-5.4"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"


def setting(name):
    return os.getenv(name, "").strip()


def provider_name():
    requested = setting("AI_PROVIDER").lower() or "auto"
    if requested in {"openai", "anthropic"}:
        return requested
    if requested != "auto":
        return None
    if setting("OPENAI_API_KEY"):
        return "openai"
    if setting("ANTHROPIC_API_KEY"):
        return "anthropic"
    return None


def model_name(stage):
    if provider_name() == "anthropic":
        return (setting("REDESIGN_MODEL") if stage == "redesign" else "") or setting("VLM_MODEL") or DEFAULT_ANTHROPIC_MODEL
    override = "OPENAI_REDESIGN_MODEL" if stage == "redesign" else "OPENAI_VISION_MODEL"
    return setting(override) or setting("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL


def configuration_error():
    if setting("VIBE_MOCK") == "1":
        return "LLM generation is disabled by VIBE_MOCK=1. Set VIBE_MOCK=0 and configure OPENAI_API_KEY or ANTHROPIC_API_KEY in .env."
    requested = setting("AI_PROVIDER").lower() or "auto"
    if requested not in {"auto", "openai", "anthropic"}:
        return "AI_PROVIDER must be auto, openai or anthropic in .env."
    provider = provider_name()
    if not provider:
        return "Set OPENAI_API_KEY (OpenAI) or ANTHROPIC_API_KEY (Anthropic) in .env to generate websites."
    key_name = "OPENAI_API_KEY" if provider == "openai" else "ANTHROPIC_API_KEY"
    if not setting(key_name):
        return f"The selected provider needs {key_name} in .env."
    return None


def available():
    return configuration_error() is None


def openai_content(content):
    """Convert the internal normalized image/text blocks at the provider boundary."""
    converted = []
    for block in content:
        if block["type"] == "text":
            converted.append({"type": "input_text", "text": block["text"]})
        elif block["type"] == "image":
            source = block["source"]
            if source["type"] != "base64" or source["media_type"] != "image/jpeg":
                raise ValueError("Only normalized inline JPEG images are supported.")
            converted.append({"type": "input_image", "image_url": "data:image/jpeg;base64," + source["data"], "detail": "auto"})
        else:
            raise ValueError("Unsupported model input block.")
    return converted


async def request_openai(system, content, validator, *, model, max_tokens=2200, timeout=30, attempt_timeout=30):
    """Two bounded attempts, including invalid JSON/schema or incomplete streams."""
    converted = openai_content(content)
    # The API requires JSON in input text even when instructions already request it.
    if not any(block["type"] == "input_text" and "json" in block["text"].lower() for block in converted):
        converted.append({"type": "input_text", "text": "Return only valid JSON matching the requested contract."})
    inputs = [{"role": "user", "content": converted}]
    async with AsyncOpenAI(api_key=setting("OPENAI_API_KEY"), base_url="https://api.openai.com/v1",
                           timeout=timeout, max_retries=0) as client:
        for attempt in range(2):
            try:
                async def receive():
                    stream = await client.responses.create(
                        model=model, instructions=system + "\nReturn only JSON.",
                        input=inputs, max_output_tokens=max_tokens, stream=True,
                        text={"format": {"type": "json_object"}}, store=False,
                    )
                    async with stream:
                        async for event in stream:
                            if event.type == "response.completed":
                                response = event.response
                                if response.status != "completed" or not response.output_text:
                                    raise ValueError("Model response is incomplete or empty.")
                                return response.output_text
                            if event.type in {"response.failed", "response.incomplete", "error"}:
                                raise ValueError("Model response failed or was incomplete.")
                    raise ValueError("Model stream ended without a completed response.")
                text = await asyncio.wait_for(receive(), timeout=attempt_timeout)
                return validator(json.loads(text))
            except asyncio.CancelledError:
                raise
            except Exception as error:
                # Never expose keys, images, prompts or upstream response bodies in logs.
                logger.warning("OpenAI attempt %d failed (%s)", attempt + 1, type(error).__name__)
    raise RuntimeError("OpenAI could not return valid output after retry. Check your key, model access and connection.")
