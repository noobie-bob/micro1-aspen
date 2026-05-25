from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from flask import Flask, jsonify, request
from pydantic import BaseModel, EmailStr, ValidationError


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ResetRequest(BaseModel):
    email: EmailStr


class ResetConfirmRequest(BaseModel):
    token: str
    new_password: str


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

app = Flask(__name__)


def _json_error(status_code: int, detail: str):
    response = jsonify({"detail": detail})
    response.status_code = status_code
    return response


def _parse_payload(model):
    try:
        data = request.get_json(force=True)
        return model(**data)
    except ValidationError as exc:
        response = jsonify({"detail": exc.errors()})
        response.status_code = 422
        return response
    except Exception:
        response = jsonify({"detail": "Invalid JSON"})
        response.status_code = 422
        return response


def _bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise ValueError("missing session")
    return authorization.removeprefix("Bearer ")


def _current_user(authorization: Optional[str]) -> User:
    try:
        session_id = _bearer_token(authorization)
    except ValueError:
        raise PermissionError("missing session")

    email = state.sessions.get(session_id)
    if not email or email not in state.users:
        raise PermissionError("invalid session")
    return state.users[email]


@app.post("/auth/login")
def login():
    payload = _parse_payload(LoginRequest)
    if not isinstance(payload, LoginRequest):
        return payload

    user = state.users.get(payload.email)
    if not user or user.password != payload.password:
        return _json_error(401, "bad credentials")

    session_id = secrets.token_urlsafe(24)
    state.sessions[session_id] = user.email
    return jsonify({"access_token": session_id, "token_type": "bearer"})


@app.get("/auth/me")
def me():
    authorization = request.headers.get("Authorization")

    try:
        user = _current_user(authorization)
    except PermissionError as exc:
        return _json_error(401, str(exc))

    return jsonify({"email": user.email})


@app.post("/auth/password/forgot")
def forgot_password():
    payload = _parse_payload(ResetRequest)
    if not isinstance(payload, ResetRequest):
        return payload

    user = state.users.get(payload.email)
    if not user:
        return jsonify({"ok": True, "message": "If the account exists, a reset link was sent."})

    token = secrets.token_urlsafe(24)

    user.reset_tokens.append(token)
    state.sent_reset_emails.append({"email": user.email, "token": token})

    response = jsonify({"ok": True, "message": "If the account exists, a reset link was sent."})
    response.status_code = 202
    return response


@app.post("/auth/password/reset")
def reset_password():
    payload = _parse_payload(ResetConfirmRequest)
    if not isinstance(payload, ResetConfirmRequest):
        return payload

    for user in state.users.values():
        if payload.token in user.reset_tokens:
            user.password = payload.new_password
            return jsonify({"ok": True})

    return _json_error(400, "invalid reset token")


@app.get("/__test__/sent-reset-emails")
def sent_reset_emails():
    return jsonify({"emails": list(state.sent_reset_emails)})


@app.post("/__test__/reset-state")
def reset_state():
    state.reset()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)