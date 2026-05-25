from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sanic import Sanic
from sanic.request import Request
from sanic.response import json as sanic_json

try:
    app = Sanic.get_app("projhub")
except Exception:
    app = Sanic("projhub", configure_logging=False)


@dataclass
class User:
    email: str
    password: str
    reset_tokens: List[str] = field(default_factory=list)


@dataclass
class InMemoryState:
    users: Dict[str, User] = field(default_factory=dict)
    sessions: Dict[str, str] = field(default_factory=dict)
    sent_reset_emails: List[Dict[str, str]] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def reset(self) -> None:
        with self.lock:
            self.users.clear()
            self.sessions.clear()
            self.sent_reset_emails.clear()
            self.users["alice@example.com"] = User(
                email="alice@example.com",
                password="old-password",
            )
            self.users["bob@example.com"] = User(
                email="bob@example.com",
                password="bob-password",
            )


state = InMemoryState()
state.reset()


def _bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return auth.removeprefix("Bearer ")


def _current_user(request: Request) -> Optional[User]:
    token = _bearer_token(request)
    if not token:
        return None
    email = state.sessions.get(token)
    if not email or email not in state.users:
        return None
    return state.users[email]


@app.post("/auth/login")
async def login(request: Request):
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return sanic_json({"detail": "Missing fields"}, status=422)
    user = state.users.get(email)
    if not user or user.password != password:
        return sanic_json({"detail": "bad credentials"}, status=401)
    session_id = secrets.token_urlsafe(24)
    state.sessions[session_id] = user.email
    return sanic_json({"access_token": session_id, "token_type": "bearer"})


@app.get("/auth/me")
async def me(request: Request):
    user = _current_user(request)
    if not user:
        return sanic_json({"detail": "invalid session"}, status=401)
    return sanic_json({"email": user.email})


@app.post("/auth/password/forgot")
async def forgot_password(request: Request):
    data = request.json or {}
    email = data.get("email")
    if not email:
        return sanic_json({"detail": "Missing email"}, status=422)
    user = state.users.get(email)
    if not user:
        return sanic_json({"ok": True, "message": "If the account exists, a reset link was sent."})
    token = secrets.token_urlsafe(24)
    user.reset_tokens.append(token)
    state.sent_reset_emails.append({"email": user.email, "token": token})
    return sanic_json(
        {"ok": True, "message": "If the account exists, a reset link was sent."},
        status=202,
    )


@app.post("/auth/password/reset")
async def reset_password(request: Request):
    data = request.json or {}
    token = data.get("token")
    new_password = data.get("new_password")
    if not token or not new_password:
        return sanic_json({"detail": "Missing fields"}, status=422)
    for user in state.users.values():
        if token in user.reset_tokens:
            user.password = new_password
            return sanic_json({"ok": True})
    return sanic_json({"detail": "invalid reset token"}, status=400)


@app.get("/__test__/sent-reset-emails")
async def sent_reset_emails(request: Request):
    return sanic_json({"emails": list(state.sent_reset_emails)})


@app.post("/__test__/reset-state")
async def reset_state_route(request: Request):
    state.reset()
    return sanic_json({"ok": True})
