from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal
import asyncio
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.imaging import prepare_image
from backend.schemas import BaselineProfile, Choice, ChoiceRequest, ExtractResponse, ResetRequest, SessionRequest, VibeTokens
from backend.session import SessionStore
from backend import vlm
from backend.redesign import load_catalog, router as redesign_router

ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATH = ROOT / "demo_site/vibe.json"
load_dotenv(ROOT / ".env")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app):
    from backend.image_db import ImageDB
    app.state.images = ImageDB()
    app.state.sessions = SessionStore()
    app.state.design_slots = asyncio.Semaphore(2)
    try:
        yield
    finally:
        tasks = [session.redesign_task for session in app.state.sessions.sessions.values() if session.redesign_task and not session.redesign_task.done()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(title="Doodle2Design", lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=False)


@app.middleware("http")
async def local_headers(request: Request, call_next):
    length = request.headers.get("content-length", "0")
    if length.isdigit() and int(length) > 26*1024*1024:
        return JSONResponse({"detail": "Upload at most 3 images, 8 MB each."}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if "Content-Security-Policy" not in response.headers:
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; frame-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/config")
def config():
    return {"offline": vlm.mock_mode(), "generation_available": not vlm.mock_mode(), "design_themes": len(load_catalog())}


@app.post("/api/session", status_code=201)
async def create_session():
    return {"session_id": app.state.sessions.create().id}


@app.post("/api/baseline", response_model=BaselineProfile)
async def baseline(session_id: Annotated[str, Form()], mode: Annotated[Literal["draw", "upload"], Form()], files: Annotated[list[UploadFile], File()]):
    session = app.state.sessions.get(session_id)
    if not 1 <= len(files) <= (1 if mode == "draw" else 3):
        raise HTTPException(422, "Draw requires one image; upload accepts 1 to 3 images.")
    images = []
    try:
        for file in files:
            data = await file.read(8*1024*1024+1)
            if len(data) > 8*1024*1024:
                raise HTTPException(413, "Each image must be at most 8 MB.")
            if file.content_type not in {"image/png", "image/jpeg", "image/webp"}:
                raise HTTPException(422, "Use PNG, JPG or WebP images.")
            try:
                images.append(prepare_image(data))
            except ValueError as error:
                raise HTTPException(422, str(error)) from error
    finally:
        for file in files:
            await file.close()
    async with session.lock:
        if session.baseline:
            raise HTTPException(409, "This session already has a baseline. Reset before starting again.")
        profile, degraded = await vlm.analyze_baseline(images)
        pairs, planning_degraded = await vlm.plan_comparisons(app.state.images, profile, session.id)
        session.images, session.baseline, session.pairs = images, profile, pairs
        session.degraded = degraded or planning_degraded
        return profile


@app.get("/api/ab/next")
async def next_pair(session_id: str, prefetch: bool = False):
    session = app.state.sessions.get(session_id)
    if not session.baseline:
        raise HTTPException(409, "Submit your drawing or references first.")
    index = len(session.choices) + int(prefetch)
    return session.pairs[index] if index < 10 else {"done": True}


@app.post("/api/ab/choice")
async def choose(data: ChoiceRequest):
    session = app.state.sessions.get(data.session_id)
    async with session.lock:
        if not session.baseline:
            raise HTTPException(409, "Submit a baseline first.")
        if data.round <= len(session.choices):
            old = session.choices[data.round-1]
            if (old.winner_id, old.loser_id) == (data.winner_id, data.loser_id):
                return {"ok": True, "round": data.round, "total": 10}
            raise HTTPException(409, "That round already has a different choice.")
        if data.round != len(session.choices)+1:
            raise HTTPException(409, "Choose the current round before continuing.")
        pair = session.pairs[data.round-1]
        if data.winner_id == data.loser_id or {data.winner_id, data.loser_id} != {pair.left_id, pair.right_id}:
            raise HTTPException(409, "Choose one of the two images in this round.")
        session.choices.append(Choice(round=data.round, winner_id=data.winner_id, loser_id=data.loser_id, category=pair.category))
        return {"ok": True, "round": data.round, "total": 10}


@app.post("/api/extract", response_model=ExtractResponse)
async def extract(data: SessionRequest):
    session = app.state.sessions.get(data.session_id)
    async with session.lock:
        if len(session.choices) != 10:
            raise HTTPException(409, "Complete all 10 comparisons before extracting a theme.")
        if session.result:
            result = session.result
            tokens = result.tokens
        else:
            tokens, degraded = await vlm.extract_theme(session, app.state.images)
            result = ExtractResponse(tokens=tokens, baseline=session.baseline, degraded=session.degraded or degraded)
        temporary = TOKEN_PATH.with_suffix(".tmp")
        temporary.write_text(tokens.model_dump_json(indent=2), encoding="utf-8")
        os.replace(temporary, TOKEN_PATH)
        session.result = result
        return result


@app.get("/api/tokens", response_model=VibeTokens)
def tokens():
    if not TOKEN_PATH.exists():
        raise HTTPException(404, "No theme has been extracted yet.")
    return VibeTokens.model_validate_json(TOKEN_PATH.read_text(encoding="utf-8"))


@app.post("/api/reset")
async def reset(data: ResetRequest):
    session = app.state.sessions.get(data.session_id)
    async with session.lock:
        if not data.demo_only:
            session.clear()
        TOKEN_PATH.unlink(missing_ok=True)
    return {"ok": True}


app.include_router(redesign_router)


for route, directory in (("/images", "images"), ("/demo", "demo_site"), ("/", "frontend")):
    (ROOT / directory).mkdir(exist_ok=True)
    app.mount(route, StaticFiles(directory=ROOT / directory, html=True), name=directory)
