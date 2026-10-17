import asyncio
import json

import pytest

from backend import ai_provider, redesign
from test_openai_provider import completed, fake_sdk
from test_redesign import design


def test_match_request_constrains_fields_titles_and_reason_length(monkeypatch):
    calls, _ = fake_sdk(monkeypatch, [[completed(json.dumps({"theme": "Botanical", "reason": "Calm natural shapes."}))]])
    asyncio.run(redesign.request_model("JSON", [], redesign.validate_match))
    format = calls[0]["text"]["format"]
    assert format["type"] == "json_schema" and format["strict"] is True
    schema = format["schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]["theme"]["enum"]) == set(redesign.load_catalog())
    assert schema["properties"]["reason"]["maxLength"] == 1200


def test_website_request_constrains_generated_artifact_fields(monkeypatch):
    calls, _ = fake_sdk(monkeypatch, [[completed(json.dumps(design()))]])
    asyncio.run(redesign.request_model("JSON", [], redesign.GeneratedDesign.model_validate))
    format = calls[0]["text"]["format"]
    assert format["type"] == "json_schema" and format["strict"] is True
    assert set(format["schema"]["required"]) == {"summary", "html", "css", "javascript"}


def test_validation_retry_includes_safe_correction_feedback(monkeypatch, caplog):
    bad = {"theme": "Botanical", "reason": "private-value-" * 150}
    good = {"theme": "Botanical", "reason": "Calm natural shapes."}
    calls, _ = fake_sdk(monkeypatch, [[completed(json.dumps(bad))], [completed(json.dumps(good))]])
    asyncio.run(redesign.request_model("JSON", [], redesign.validate_match))
    assert "reason" in calls[1]["instructions"] and "string_too_long" in calls[1]["instructions"]
    assert "private-value" not in calls[1]["instructions"]
    assert "string_too_long" in caplog.text and "private-value" not in caplog.text


def test_invalid_model_output_is_not_reported_as_a_key_failure(monkeypatch):
    fake_sdk(monkeypatch, [[completed('{"wrong":"shape"}')], [completed('{"wrong":"shape"}')]])
    with pytest.raises(ai_provider.ModelRequestError) as error:
        asyncio.run(redesign.request_model("JSON", [], redesign.validate_match))
    assert error.value.kind == "invalid_output"
    async def fail(*args):
        raise error.value
    monkeypatch.setattr(redesign, "generate", fail)
    state = {"phase": "queued", "theme": None}
    asyncio.run(redesign.run_job(None, None, asyncio.Semaphore(1), state))
    assert state["phase"] == "error"
    assert "Theme matching" in state["error"] and "format" in state["error"]
    assert "API key" not in state["error"]


def test_semantic_html_checks_still_require_all_business_sections(monkeypatch):
    invalid = {**design(), "html": design()["html"].replace('id="pricing"', 'id="other"')}
    calls, _ = fake_sdk(monkeypatch, [[completed(json.dumps(invalid))], [completed(json.dumps(design()))]])
    result = asyncio.run(redesign.request_model("JSON", [], redesign.GeneratedDesign.model_validate))
    assert result.html == design()["html"]
    assert "html:value_error" in calls[1]["instructions"]
