"""The redesign must come from a selected document and an actual model response."""
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend import redesign
from backend.session import Session
from backend.mock import baseline_profile, extract_tokens
from backend.schemas import ExtractResponse
from test_api import client, baseline, complete, upload


def design():
    return {
        "summary": "A botanical garden with sculpted controls and swaying trees.",
        "html": '<header>Northwind Analytics</header><main><h1>Clarity</h1>'
                '<section id="features">Real-time insights</section>'
                '<section id="dashboard">$124,800 8,492 4.82%</section>'
                '<section id="pricing">$49 $249 $599</section>'
                '<section id="contact"><form id="contact-form"><label>Email<input type="email" required></label>'
                '<button>Contact</button><p role="status"></p></form></section></main>',
        "css": "body{background:#edf2e7}button{border-radius:30px}",
        "javascript": "document.querySelector('form').addEventListener('submit',e=>e.preventDefault());",
    }


def test_catalog_uses_exact_document_titles_and_complete_briefs():
    themes = redesign.load_catalog()
    assert len(themes) == 30
    assert {"Botanical", "Professional", "Neo Brutalism", "Kinetic", "Art Deco"} <= themes.keys()
    for title, theme in themes.items():
        assert theme["source"] == title + ".docx"
        assert len(theme["instructions"]) > 2500
        assert "<role>" not in theme["instructions"]
        import hashlib
        assert hashlib.sha256(Path("design_prompts", theme["source"]).read_bytes()).hexdigest() == theme["sha256"]
    assert "200px" in themes["Botanical"]["instructions"]


def test_model_cannot_invent_a_theme():
    with pytest.raises(ValueError, match="catalog"):
        redesign.validate_match({"theme": "Some New Theme", "reason": "Good match"})
    assert redesign.validate_match({"theme": "Botanical", "reason": "Calm and organic."}).theme == "Botanical"


def test_generation_uses_full_selected_brief_and_taste_evidence(monkeypatch):
    from backend.image_db import ImageDB
    from backend.schemas import Choice
    db = ImageDB()
    image = upload("#5c8450")[1][1]
    session = Session(id="pipeline", images=[image])
    session.baseline = baseline_profile(session.images)
    session.result = ExtractResponse(tokens=extract_tokens(session.images), baseline=session.baseline, degraded=True)
    identifiers = list(db.images)[:2]
    session.choices = [Choice(round=i, category=db.images[identifiers[0]]["category"],
                             winner_id=identifiers[0], loser_id=identifiers[1]) for i in range(1, 11)]
    calls = []
    async def fake_request(system, content, validator, **options):
        calls.append((system, content, options))
        return validator({"theme": "Botanical", "reason": "The calm organic mood fits."} if len(calls) == 1 else design())
    monkeypatch.setattr(redesign, "request_model", fake_request)
    status = {"phase": "matching", "theme": None, "reason": None, "summary": None, "error": None}
    result = asyncio.run(redesign.generate(session, db, status))
    assert status["phase"] == "generating" and status["theme"] == "Botanical"
    match_text = calls[0][1][-1]["text"]
    assert all(title in match_text for title in redesign.load_catalog())
    assert "rejected" in match_text and "baseline" in match_text
    assert sum(block["type"] == "image" for block in calls[0][1]) == 11
    prompt = calls[1][1][-1]["text"]
    assert redesign.load_catalog()["Botanical"]["instructions"] in prompt
    assert "Northwind" in prompt and "$124,800" in prompt
    assert result.css == design()["css"]  # Model output, not a preset renderer.
    assert calls[1][2]["max_tokens"] >= 12000


def test_preview_wraps_generated_code_and_rejects_document_breakouts():
    value = redesign.GeneratedDesign.model_validate(design())
    document = redesign.render_document(value)
    assert 'http-equiv="Content-Security-Policy"' in document
    from html import unescape
    assert "connect-src 'none'" in unescape(document)
    assert "prefers-reduced-motion" in document
    assert value.html in document and value.css in document
    for bad in ('<meta http-equiv="refresh" content="0;url=https://example.com">', "<iframe src='/api/config'></iframe>", "<script src='/js/app.js'></script>"):
        with pytest.raises(ValueError):
            redesign.GeneratedDesign.model_validate({**design(), "html": bad + design()["html"]})
    with pytest.raises(ValueError):
        redesign.GeneratedDesign.model_validate({**design(), "css": "</style><script>alert(1)</script>"})


def test_generation_requires_complete_profile_and_key(client, monkeypatch):
    sid = client.post("/api/session").json()["session_id"]
    assert client.post("/api/redesign", json={"session_id": sid}).status_code == 409
    sid = baseline(client)
    complete(client, sid)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.post("/api/redesign", json={"session_id": sid})
    assert response.status_code == 503 and "ANTHROPIC_API_KEY" in response.json()["detail"]
    assert client.get("/api/redesign/preview", params={"session_id": sid}).status_code == 409


def test_job_is_cached_isolated_and_reset_cancels_artifact(client, monkeypatch):
    calls = []
    async def fake_generate(session, db, state):
        calls.append(session.id)
        state.update(theme="Botanical", reason="Soft organic mood.")
        await asyncio.sleep(0.01)
        return redesign.GeneratedDesign.model_validate(design())
    monkeypatch.setattr(redesign, "generate", fake_generate)
    sid = baseline(client)
    complete(client, sid)
    monkeypatch.setattr(redesign.vlm, "mock_mode", lambda: False)
    first = client.post("/api/redesign", json={"session_id": sid})
    assert first.status_code == 202
    assert client.post("/api/redesign", json={"session_id": sid}).status_code in (200, 202)
    import time
    for _ in range(100):
        state = client.get("/api/redesign", params={"session_id": sid}).json()
        if state["phase"] == "ready": break
        time.sleep(0.01)
    assert state["phase"] == "ready", state
    assert calls == [sid]
    assert state["theme"] == "Botanical" and "html" not in state
    preview = client.get(state["preview_url"])
    policy = preview.headers["content-security-policy"]
    assert "sandbox allow-scripts" in policy and "allow-same-origin" not in policy
    assert "connect-src 'none'" in policy and "frame-src 'none'" in policy
    assert design()["html"] in preview.text
    assert "sandbox" not in client.get("/").headers["content-security-policy"]
    download = client.get(state["download_url"])
    assert "attachment" in download.headers["content-disposition"]
    assert "Content-Security-Policy" in download.text
    assert client.post("/api/redesign", json={"session_id": sid}).json()["phase"] == "ready"
    client.post("/api/reset", json={"session_id": sid})
    assert client.get(state["preview_url"]).status_code == 409


def test_streaming_request_retries_invalid_output(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-never-transmitted")
    responses = ["not-json", json.dumps(design())]
    requests = []
    class Stream:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get_final_message(self):
            return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=responses.pop(0))])
    class Client:
        def __init__(self, **kwargs):
            assert kwargs["max_retries"] == 0
            self.messages = self
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        def stream(self, **kwargs):
            requests.append(kwargs)
            return Stream()
    monkeypatch.setattr(redesign, "AsyncAnthropic", Client)
    result = asyncio.run(redesign.request_model("system", [], redesign.GeneratedDesign.model_validate, max_tokens=16000))
    assert result.html == design()["html"] and len(requests) == 2
    assert requests[0]["max_tokens"] == 16000


def test_failed_job_surfaces_error_and_clear_cancels_running_work(monkeypatch):
    async def scenario():
        session = Session(id="cancel-test")
        state = {"phase": "queued"}
        async def fail(*args):
            raise RuntimeError("private transport details must not reach the browser")
        monkeypatch.setattr(redesign, "generate", fail)
        await redesign.run_job(session, None, asyncio.Semaphore(1), state)
        assert state["phase"] == "error"
        assert "private transport" not in state["error"]
        entered = asyncio.Event()
        cancelled = asyncio.Event()
        async def wait_forever(*args):
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        monkeypatch.setattr(redesign, "generate", wait_forever)
        session.redesign = {"phase": "queued"}
        session.redesign_task = asyncio.create_task(redesign.run_job(session, None, asyncio.Semaphore(1), session.redesign))
        task = session.redesign_task
        await entered.wait()
        session.clear()
        await asyncio.gather(task, return_exceptions=True)
        assert cancelled.is_set()
        assert session.redesign is None and session.redesign_task is None
    asyncio.run(scenario())
