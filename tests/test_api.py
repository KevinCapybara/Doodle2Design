from io import BytesIO
from pathlib import Path
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas import VibeTokens
from backend.imaging import contrast_ratio


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.main.TOKEN_PATH", tmp_path / "vibe.json")
    with TestClient(app) as value:
        yield value


def upload(color="#20253c"):
    stream = BytesIO()
    Image.new("RGB", (100, 100), color).save(stream, "PNG")
    return ("files", ("test.png", stream.getvalue(), "image/png"))


def baseline(client, mode="upload", files=None):
    sid = client.post("/api/session").json()["session_id"]
    response = client.post("/api/baseline", data={"session_id": sid, "mode": mode}, files=files or [upload()])
    assert response.status_code == 200, response.text
    return sid


def complete(client, sid):
    seen = set()
    for n in range(1, 11):
        pair = client.get("/api/ab/next", params={"session_id": sid}).json()
        assert pair["round"] == n
        assert not seen.intersection((pair["left_id"], pair["right_id"]))
        seen.update((pair["left_id"], pair["right_id"]))
        data = {"session_id": sid, "round": n, "winner_id": pair["left_id"], "loser_id": pair["right_id"]}
        assert client.post("/api/ab/choice", json=data).status_code == 200
        # Retries must not count a second choice.
        assert client.post("/api/ab/choice", json=data).status_code == 200
    assert client.get("/api/ab/next", params={"session_id": sid}).json() == {"done": True}
    response = client.post("/api/extract", json={"session_id": sid})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("mode", ["draw", "upload"])
def test_full_flow_and_reset(client, mode):
    sid = baseline(client, mode)
    result = complete(client, sid)
    tokens = VibeTokens.model_validate(result["tokens"])
    assert result["degraded"] is True
    assert contrast_ratio(tokens.colors.bg, tokens.colors.text) >= 4.5
    from backend.main import TOKEN_PATH
    assert TOKEN_PATH.exists()
    assert client.get("/api/tokens").json() == result["tokens"]
    assert client.post("/api/extract", json={"session_id": sid}).json() == result
    assert client.post("/api/reset", json={"session_id": sid}).status_code == 200
    assert not TOKEN_PATH.exists()
    assert client.get("/api/tokens").status_code == 404
    assert client.get("/api/ab/next", params={"session_id": sid}).status_code == 409


def test_unknown_session_and_phase_guards(client):
    assert client.post("/api/extract", json={"session_id": "missing"}).status_code == 404
    sid = client.post("/api/session").json()["session_id"]
    assert client.post("/api/extract", json={"session_id": sid}).status_code == 409
    sid = baseline(client)
    assert client.post("/api/ab/choice", json={"session_id": sid, "round": 1, "winner_id": "fake", "loser_id": "fake"}).status_code == 409
    assert client.post("/api/extract", json={"session_id": sid}).status_code == 409


def test_upload_validation(client):
    sid = client.post("/api/session").json()["session_id"]
    data = {"session_id": sid, "mode": "upload"}
    assert client.post("/api/baseline", data=data, files=[upload()]*4).status_code == 422
    assert client.post("/api/baseline", data={**data, "mode": "draw"}, files=[upload()]*2).status_code == 422
    assert client.post("/api/baseline", data=data, files=[("files", ("bad.png", b"not an image", "image/png"))]).status_code == 422
    assert client.post("/api/baseline", data=data, files=[("files", ("huge.png", b"0"*(8*1024*1024+1), "image/png"))]).status_code == 413


def test_prefetch_does_not_skip_round(client):
    sid = baseline(client)
    assert client.get("/api/ab/next", params={"session_id": sid, "prefetch": True}).json()["round"] == 2
    assert client.get("/api/ab/next", params={"session_id": sid}).json()["round"] == 1


def test_demo_reset_keeps_theme_available_to_reapply(client):
    sid = baseline(client)
    result = complete(client, sid)
    assert client.post("/api/reset", json={"session_id": sid, "demo_only": True}).status_code == 200
    assert client.get("/api/tokens").status_code == 404
    assert client.post("/api/extract", json={"session_id": sid}).json() == result
    assert client.get("/api/tokens").json() == result["tokens"]
