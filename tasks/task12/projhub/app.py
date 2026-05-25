from __future__ import annotations

import json
import secrets
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from robyn import Robyn, Request, Response

app = Robyn(__file__)


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


def _json_resp(data: dict, status_code: int = 200) -> Response:
    return Response(
        status_code=status_code,
        headers={"Content-Type": "application/json"},
        description=json.dumps(data),
    )


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
async def login(request: Request) -> Response:
    try:
        body = request.body
        data = json.loads(body if isinstance(body, str) else body.decode())
    except Exception:
        return _json_resp({"detail": "Invalid JSON"}, 422)
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return _json_resp({"detail": "Missing fields"}, 422)
    user = state.users.get(email)
    if not user or user.password != password:
        return _json_resp({"detail": "bad credentials"}, 401)
    session_id = secrets.token_urlsafe(24)
    state.sessions[session_id] = user.email
    return _json_resp({"access_token": session_id, "token_type": "bearer"})


@app.get("/auth/me")
async def me(request: Request) -> Response:
    user = _current_user(request)
    if not user:
        return _json_resp({"detail": "invalid session"}, 401)
    return _json_resp({"email": user.email})


@app.post("/auth/password/forgot")
async def forgot_password(request: Request) -> Response:
    try:
        body = request.body
        data = json.loads(body if isinstance(body, str) else body.decode())
    except Exception:
        return _json_resp({"detail": "Invalid JSON"}, 422)
    email = data.get("email")
    if not email:
        return _json_resp({"detail": "Missing email"}, 422)
    user = state.users.get(email)
    if not user:
        return _json_resp({"ok": True, "message": "If the account exists, a reset link was sent."})
    token = secrets.token_urlsafe(24)
    user.reset_tokens.append(token)
    state.sent_reset_emails.append({"email": user.email, "token": token})
    return _json_resp(
        {"ok": True, "message": "If the account exists, a reset link was sent."},
        202,
    )


@app.post("/auth/password/reset")
async def reset_password(request: Request) -> Response:
    try:
        body = request.body
        data = json.loads(body if isinstance(body, str) else body.decode())
    except Exception:
        return _json_resp({"detail": "Invalid JSON"}, 422)
    token = data.get("token")
    new_password = data.get("new_password")
    if not token or not new_password:
        return _json_resp({"detail": "Missing fields"}, 422)
    for user in state.users.values():
        if token in user.reset_tokens:
            user.password = new_password
            return _json_resp({"ok": True})
    return _json_resp({"detail": "invalid reset token"}, 400)


@app.get("/__test__/sent-reset-emails")
async def sent_reset_emails(request: Request) -> Response:
    return _json_resp({"emails": list(state.sent_reset_emails)})


@app.post("/__test__/reset-state")
async def reset_state_route(request: Request) -> Response:
    state.reset()
    return _json_resp({"ok": True})


if __name__ == "__main__":
    import os
    _port = int(os.environ.get("PROJHUB_PORT", "8080"))
    app.start(host="127.0.0.1", port=_port)
