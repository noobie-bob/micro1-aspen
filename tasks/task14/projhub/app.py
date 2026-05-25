from __future__ import annotations

import json
import secrets
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from bottle import Bottle, request, response

app = Bottle()


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


def _json_resp(data: dict, status: int = 200) -> str:
    response.status = status
    response.content_type = "application/json"
    return json.dumps(data)


def _json_error(status: int, detail: str) -> str:
    return _json_resp({"detail": detail}, status)


def _bearer_token() -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return auth[7:]


def _current_user() -> Optional[User]:
    token = _bearer_token()
    if not token:
        return None
    email = state.sessions.get(token)
    if not email or email not in state.users:
        return None
    return state.users[email]


@app.post("/auth/login")
def login() -> str:
    data = request.json
    if not data or "email" not in data or "password" not in data:
        return _json_error(422, "missing fields")
    user = state.users.get(data["email"])
    if not user or user.password != data["password"]:
        return _json_error(401, "bad credentials")
    session_id = secrets.token_urlsafe(24)
    state.sessions[session_id] = user.email
    return _json_resp({"access_token": session_id, "token_type": "bearer"})


@app.get("/auth/me")
def me() -> str:
    user = _current_user()
    if not user:
        return _json_error(401, "invalid session")
    return _json_resp({"email": user.email})


@app.post("/auth/password/forgot")
def forgot_password() -> str:
    data = request.json
    if not data or "email" not in data:
        return _json_error(422, "missing fields")
    user = state.users.get(data["email"])
    if not user:
        return _json_resp({"ok": True, "message": "If the account exists, a reset link was sent."})
    token = secrets.token_urlsafe(24)
    user.reset_tokens.append(token)
    state.sent_reset_emails.append({"email": user.email, "token": token})
    return _json_resp(
        {"ok": True, "message": "If the account exists, a reset link was sent."},
        status=202,
    )


@app.post("/auth/password/reset")
def reset_password() -> str:
    data = request.json
    if not data or "token" not in data or "new_password" not in data:
        return _json_error(422, "missing fields")
    for user in state.users.values():
        if data["token"] in user.reset_tokens:
            user.password = data["new_password"]
            return _json_resp({"ok": True})
    return _json_error(400, "invalid reset token")


@app.get("/__test__/sent-reset-emails")
def sent_reset_emails() -> str:
    return _json_resp({"emails": list(state.sent_reset_emails)})


@app.post("/__test__/reset-state")
def reset_state() -> str:
    state.reset()
    return _json_resp({"ok": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
