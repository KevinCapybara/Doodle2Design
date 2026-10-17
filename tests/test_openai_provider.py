import asyncio
import json
from types import SimpleNamespace

import pytest

from backend import ai_provider, vlm, redesign
from test_api import client, baseline, complete, upload
from test_redesign import design


def test_provider_selection_and_models(monkeypatch):
    monkeypatch.setenv("VIBE_MOCK", "0")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test")
    monkeypatch.setenv("VLM_MODEL", "claude-legacy-override")
    monkeypatch.setenv("REDESIGN_MODEL", "claude-design-override")
    assert ai_provider.provider_name() == "anthropic"
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test")
    assert ai_provider.provider_name() == "openai" and not vlm.mock_mode()
    assert ai_provider.model_name("vision") == "gpt-5.4"
    assert ai_provider.model_name("redesign") == "gpt-5.4"
    monkeypatch.setenv("OPENAI_MODEL", "openai-shared")
    monkeypatch.setenv("OPENAI_VISION_MODEL", "openai-vision")
    monkeypatch.setenv("OPENAI_REDESIGN_MODEL", "openai-design")
    assert ai_provider.model_name("vision") == "openai-vision"
    assert ai_provider.model_name("redesign") == "openai-design"
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    assert ai_provider.model_name("redesign") == "claude-design-override"
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY")
    assert vlm.mock_mode()  # Never silently send data to the other configured service.
    assert "OPENAI_API_KEY" in ai_provider.configuration_error()
    monkeypatch.setenv("AI_PROVIDER", "invalid")
    assert vlm.mock_mode() and "AI_PROVIDER" in ai_provider.configuration_error()


def test_mock_mode_still_disables_both_providers(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    assert vlm.mock_mode()
    assert "VIBE_MOCK" in ai_provider.configuration_error()


def fake_sdk(monkeypatch, outputs):
    requests, streams = [], []
    class Stream:
        def __init__(self):
            self.closed = False
            self.events = iter(outputs.pop(0))
        async def __aenter__(self): return self
        async def __aexit__(self, *args): self.closed = True
        def __aiter__(self): return self
        async def __anext__(self):
            try: return next(self.events)
            except StopIteration: raise StopAsyncIteration
    class Client:
        def __init__(self, **kwargs):
            assert kwargs["api_key"] == "test-never-transmitted"
            assert kwargs["max_retries"] == 0
            self.responses = self
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def create(self, **kwargs):
            requests.append(kwargs)
            stream = Stream()
            streams.append(stream)
            return stream
    monkeypatch.setattr(ai_provider, "AsyncOpenAI", Client)
    monkeypatch.setenv("OPENAI_API_KEY", "test-never-transmitted")
    monkeypatch.setenv("VIBE_MOCK", "0")
    return requests, streams


def completed(value):
    return SimpleNamespace(type="response.completed", response=SimpleNamespace(status="completed", output_text=value))


def test_openai_vision_converts_images_and_retries_bad_json(monkeypatch):
    requests, streams = fake_sdk(monkeypatch, [[completed("broken")], [completed('{"ok":true}')]])
    content = [vlm.image_block(upload()[1][1]), {"type": "text", "text": "Return JSON."}]
    value = asyncio.run(vlm.request_json("Return JSON", content, lambda raw: raw))
    assert value == {"ok": True} and len(requests) == 2
    request = requests[0]
    assert request["model"] == "gpt-5.4"
    assert request["store"] is False and request["stream"] is True
    assert request["text"]["format"]["type"] == "json_object"
    assert "tools" not in request
    image, text = request["input"][0]["content"]
    assert image["type"] == "input_image" and image["image_url"].startswith("data:image/jpeg;base64,")
    assert text == {"type": "input_text", "text": "Return JSON."}
    assert all(stream.closed for stream in streams)


def test_openai_redesign_uses_large_budget_and_own_model(monkeypatch):
    requests, _ = fake_sdk(monkeypatch, [[completed(json.dumps(design()))]])
    monkeypatch.setenv("OPENAI_REDESIGN_MODEL", "openai-design")
    result = asyncio.run(redesign.request_model("JSON", [{"type":"text","text":"JSON"}],
                         redesign.GeneratedDesign.model_validate, max_tokens=16000))
    assert result.html == design()["html"]
    assert requests[0]["model"] == "openai-design"
    assert requests[0]["max_output_tokens"] == 16000


@pytest.mark.parametrize("events", [
    [SimpleNamespace(type="response.incomplete")],
    [SimpleNamespace(type="response.failed")],
    [SimpleNamespace(type="error")],
    [],
    [completed('{"refusal":"No generated artifact"}')],
])
def test_incomplete_failed_refused_and_truncated_output_cannot_succeed(monkeypatch, events):
    requests, streams = fake_sdk(monkeypatch, [events, events])
    with pytest.raises(RuntimeError):
        asyncio.run(ai_provider.request_openai("JSON", [], redesign.GeneratedDesign.model_validate,
                                               model="gpt-5.4"))
    assert len(requests) == 2 and all(stream.closed for stream in streams)


def test_openai_only_config_and_job_metadata(client, monkeypatch):
    sid = baseline(client)
    complete(client, sid)
    monkeypatch.setenv("VIBE_MOCK", "0")
    monkeypatch.setenv("OPENAI_API_KEY", "test-never-transmitted")
    monkeypatch.setenv("OPENAI_REDESIGN_MODEL", "openai-design")
    config = client.get("/api/config").json()
    assert config["generation_available"] is True
    assert config["ai_provider"] == "openai" and config["generation_model"] == "openai-design"
    assert "test-never-transmitted" not in json.dumps(config)
    async def generate(session, db, state):
        state.update(theme="Botanical", reason="An organic mood.")
        return redesign.GeneratedDesign.model_validate(design())
    monkeypatch.setattr(redesign, "generate", generate)
    state = client.post("/api/redesign", json={"session_id": sid}).json()
    assert state["provider"] == "openai" and state["model"] == "openai-design"


def test_missing_key_message_accepts_either_provider(client):
    sid = baseline(client)
    complete(client, sid)
    result = client.post("/api/redesign", json={"session_id": sid})
    assert result.status_code == 503
    assert "OPENAI_API_KEY" in result.json()["detail"]


def test_real_openai_sdk_serializes_and_decodes_sse_without_network(monkeypatch):
    import httpx
    from openai import AsyncOpenAI as SDK
    requests = []
    event = {"type": "response.completed", "response": {
        "id": "resp_fixture", "object": "response", "created_at": 0,
        "status": "completed", "model": "gpt-5.4",
        "output": [{"type": "message", "id": "msg_fixture", "status": "completed",
                    "role": "assistant", "content": [{"type": "output_text",
                    "text": '{"ok":true}', "annotations": []}]}]}}
    async def respond(request):
        assert str(request.url) == "https://api.openai.com/v1/responses"
        assert request.headers["authorization"] == "Bearer test-never-transmitted"
        requests.append(json.loads(request.content))
        data = "event: response.completed\ndata: " + json.dumps(event) + "\n\n"
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=data)
    def client_factory(**kwargs):
        return SDK(**kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)))
    monkeypatch.setattr(ai_provider, "AsyncOpenAI", client_factory)
    monkeypatch.setenv("OPENAI_API_KEY", "test-never-transmitted")
    value = asyncio.run(ai_provider.request_openai("JSON", [{"type":"text","text":"JSON"}],
                        lambda raw: raw, model="gpt-5.4"))
    assert value == {"ok": True} and len(requests) == 1
    assert requests[0]["store"] is False


def test_full_calibration_and_generation_use_only_openai(client, monkeypatch):
    import time
    from backend.mock import baseline_profile, extract_tokens
    image = upload("#5c8450")[1][1]
    from backend.selection import plan_pairs
    planned = plan_pairs(client.app.state.images, baseline_profile([image]).preferred_categories, "openai-test")
    outputs = [baseline_profile([image]).model_dump_json(),
               json.dumps({"pairs": [pair.model_dump() for pair in planned]}),
               extract_tokens([image]).model_dump_json(),
               json.dumps({"theme": "Botanical", "reason": "Calm organic shapes and natural textures."}),
               json.dumps(design())]
    requests, _ = fake_sdk(monkeypatch, [[completed(value)] for value in outputs])
    sid = baseline(client)
    result = complete(client, sid)
    assert result["degraded"] is False
    assert client.post("/api/redesign", json={"session_id": sid}).status_code == 202
    for _ in range(100):
        status = client.get("/api/redesign", params={"session_id": sid}).json()
        if status["phase"] in {"ready", "error"}:
            break
        time.sleep(0.01)
    assert status["phase"] == "ready", status
    assert status["provider"] == "openai" and status["theme"] == "Botanical"
    assert len(requests) == 5 and all(request["model"] == "gpt-5.4" for request in requests)
    assert requests[-1]["max_output_tokens"] == 16000
    assert client.get(status["preview_url"]).status_code == 200



def test_image_only_input_gets_required_json_instruction(monkeypatch):
    requests, _ = fake_sdk(monkeypatch, [[completed('{"ok":true}')]])
    asyncio.run(ai_provider.request_openai("JSON", [vlm.image_block(upload()[1][1])],
                lambda raw: raw, model="gpt-5.4"))
    content = requests[0]["input"][0]["content"]
    assert content[0]["type"] == "input_image"
    assert content[-1]["type"] == "input_text" and "JSON" in content[-1]["text"]
