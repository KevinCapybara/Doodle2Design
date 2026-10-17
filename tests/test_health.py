from fastapi.testclient import TestClient
from backend.main import app


def test_health_and_static_shell():
    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"ok": True}
        assert "Doodle2Design" in client.get("/").text
        assert client.get("/demo/").status_code == 200
