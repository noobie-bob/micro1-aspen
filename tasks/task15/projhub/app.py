from __future__ import annotations

import json
import secrets
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import cherrypy


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


def _json_resp(data: dict, status: int = 200) -> bytes:
    cherrypy.response.headers["Content-Type"] = "application/json"
    cherrypy.response.status = status
    return json.dumps(data).encode()


def _json_error(status: int, detail: str) -> bytes:
    return _json_resp({"detail": detail}, status)


def _bearer_token() -> Optional[str]:
    auth = cherrypy.request.headers.get("Authorization", "")
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


class Root:
    @cherrypy.expose
    def default(self, *vpath, **kwargs) -> bytes:
        path = "/" + "/".join(vpath)
        method = cherrypy.request.method
        raw_body = cherrypy.request.body.read()
        data: dict = {}
        if raw_body:
            try:
                data = json.loads(raw_body)
            except Exception:
                pass

        if path == "/auth/login" and method == "POST":
            return _handle_login(data)
        if path == "/auth/me" and method == "GET":
            return _handle_me()
        if path == "/auth/password/forgot" and method == "POST":
            return _handle_forgot(data)
        if path == "/auth/password/reset" and method == "POST":
            return _handle_reset(data)
        if path == "/__test__/sent-reset-emails":
            return _json_resp({"emails": list(state.sent_reset_emails)})
        if path == "/__test__/reset-state":
            state.reset()
            return _json_resp({"ok": True})
        raise cherrypy.HTTPError(404)


def _handle_login(data: dict) -> bytes:
    if "email" not in data or "password" not in data:
        return _json_error(422, "missing fields")
    user = state.users.get(data["email"])
    if not user or user.password != data["password"]:
        return _json_error(401, "bad credentials")
    session_id = secrets.token_urlsafe(24)
    state.sessions[session_id] = user.email
    return _json_resp({"access_token": session_id, "token_type": "bearer"})


def _handle_me() -> bytes:
    user = _current_user()
    if not user:
        return _json_error(401, "invalid session")
    return _json_resp({"email": user.email})


def _handle_forgot(data: dict) -> bytes:
    if "email" not in data:
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


def _handle_reset(data: dict) -> bytes:
    if "token" not in data or "new_password" not in data:
        return _json_error(422, "missing fields")
    for user in state.users.values():
        if data["token"] in user.reset_tokens:
            user.password = data["new_password"]
            return _json_resp({"ok": True})
    return _json_error(400, "invalid reset token")


if __name__ == "__main__":
    cherrypy.config.update({
        "server.socket_host": "127.0.0.1",
        "server.socket_port": 8080,
    })
    cherrypy.quickstart(Root(), "/")
