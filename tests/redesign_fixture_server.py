"""Optional browser QA server. Never contacts a model service."""
import asyncio
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["VIBE_MOCK"] = "0"
os.environ["AI_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = "fixture-not-a-real-key"

from backend import redesign, vlm
from backend.main import app
from test_redesign import design

async def unavailable(*args, **kwargs):
    raise RuntimeError("Browser fixture uses offline taste analysis")

async def model(system, content, validator, **kwargs):
    await asyncio.sleep(0.2)
    if kwargs.get("max_tokens", 2200) < 12000:
        return validator({"theme": "Botanical", "reason": "The green organic palette and calm visual preferences suit the Botanical brief."})
    value = design()
    value["html"] = value["html"].replace("<h1>Clarity</h1>", '<svg aria-hidden="true" viewBox="0 0 100 100" class="tree"><path d="M50 0 10 75h30v25h20V75h30Z" fill="#4d7653"/></svg><h1>Clarity, naturally.</h1>')
    value["css"] += ".tree{width:100px;opacity:.25;animation:sway 3s ease-in-out infinite alternate}@keyframes sway{to{transform:rotate(5deg)}}body{padding:24px;font:16px system-ui}section{padding:24px 0}"
    value["javascript"] = """
try{void parent.document.body;document.body.dataset.parentAccess='allowed'}catch{document.body.dataset.parentAccess='blocked'}
fetch('/api/config').then(()=>document.body.dataset.network='allowed').catch(()=>document.body.dataset.network='blocked');
document.getElementById('contact-form').addEventListener('submit',e=>{e.preventDefault();e.target.querySelector('[role=status]').textContent='Demo only. No message was sent.'});
"""
    return validator(value)

vlm.mock_mode = lambda: False
vlm.request_json = unavailable
redesign.request_model = model

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="warning")
