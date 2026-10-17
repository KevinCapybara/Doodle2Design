import asyncio
from dataclasses import dataclass, field
import time
from uuid import uuid4

from fastapi import HTTPException
from backend.schemas import ABPair, BaselineProfile, Choice, ExtractResponse


@dataclass
class Session:
    id: str
    images: list[bytes] = field(default_factory=list)
    baseline: BaselineProfile | None = None
    pairs: list[ABPair] = field(default_factory=list)
    choices: list[Choice] = field(default_factory=list)
    result: ExtractResponse | None = None
    redesign: dict | None = None
    redesign_task: asyncio.Task | None = None
    degraded: bool = False
    touched: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def clear(self):
        if self.redesign_task and not self.redesign_task.done():
            self.redesign_task.cancel()
        self.redesign_task = None
        self.redesign = None
        self.images.clear()
        self.baseline = None
        self.pairs.clear()
        self.choices.clear()
        self.result = None
        self.degraded = False


class SessionStore:
    def __init__(self):
        self.sessions = {}

    def create(self):
        stale = [key for key, value in self.sessions.items() if time.monotonic()-value.touched > 7200 and not value.lock.locked() and not (value.redesign_task and not value.redesign_task.done())]
        for key in stale:
            del self.sessions[key]
        if len(self.sessions) >= 100:
            raise HTTPException(503, "Too many active sessions. Restart the local server to clear them.")
        session = Session(id=str(uuid4()))
        self.sessions[session.id] = session
        return session

    def get(self, session_id):
        if session_id not in self.sessions:
            raise HTTPException(404, "Session not found. Start a new session.")
        session = self.sessions[session_id]
        session.touched = time.monotonic()
        return session
