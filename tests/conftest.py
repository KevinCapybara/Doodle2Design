import pytest


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    # Tests never inherit real credentials or provider overrides from the host/.env.
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AI_PROVIDER", "OPENAI_MODEL",
                 "OPENAI_VISION_MODEL", "OPENAI_REDESIGN_MODEL", "VLM_MODEL", "REDESIGN_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("VIBE_MOCK", "1")
