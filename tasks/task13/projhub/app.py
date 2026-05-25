from __future__ import annotations

import json
import secrets
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import tornado.httpserver
import tornado.ioloop
import tornado.web


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


def _bearer_token(request: tornado.httpserver.HTTPRequest) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return auth[7:]


def _current_user(request: tornado.httpserver.HTTPRequest) -> Optional[User]:
    token = _bearer_token(request)
    if not token:
        return None
    email = state.sessions.get(token)
    if not email or email not in state.users:
        return None
    return state.users[email]


class BaseHandler(tornado.web.RequestHandler):
    def json_error(self, status: int, detail: str) -> None:
        self.set_status(status)
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps({"detail": detail}))

    def json_ok(self, data: dict, status: int = 200) -> None:
        self.set_status(status)
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps(data))

    def parse_json(self) -> Optional[dict]:
        try:
            return json.loads(self.request.body)
        except Exception:
            return None


class LoginHandler(BaseHandler):
    async def post(self) -> None:
        data = self.parse_json()
        if not data or "email" not in data or "password" not in data:
            self.json_error(422, "missing fields")
            return
        user = state.users.get(data["email"])
        if not user or user.password != data["password"]:
            self.json_error(401, "bad credentials")
            return
        session_id = secrets.token_urlsafe(24)
        state.sessions[session_id] = user.email
        self.json_ok({"access_token": session_id, "token_type": "bearer"})


class MeHandler(BaseHandler):
    async def get(self) -> None:
        user = _current_user(self.request)
        if not user:
            self.json_error(401, "invalid session")
            return
        self.json_ok({"email": user.email})


class ForgotPasswordHandler(BaseHandler):
    async def post(self) -> None:
        data = self.parse_json()
        if not data or "email" not in data:
            self.json_error(422, "missing fields")
            return
        user = state.users.get(data["email"])
        if not user:
            self.json_ok({"ok": True, "message": "If the account exists, a reset link was sent."})
            return
        token = secrets.token_urlsafe(24)
        user.reset_tokens.append(token)
        state.sent_reset_emails.append({"email": user.email, "token": token})
        self.json_ok(
            {"ok": True, "message": "If the account exists, a reset link was sent."},
            status=202,
        )


class ResetPasswordHandler(BaseHandler):
    async def post(self) -> None:
        data = self.parse_json()
        if not data or "token" not in data or "new_password" not in data:
            self.json_error(422, "missing fields")
            return
        for user in state.users.values():
            if data["token"] in user.reset_tokens:
                user.password = data["new_password"]
                self.json_ok({"ok": True})
                return
        self.json_error(400, "invalid reset token")


class SentEmailsHandler(BaseHandler):
    async def get(self) -> None:
        self.json_ok({"emails": list(state.sent_reset_emails)})


class ResetStateHandler(BaseHandler):
    async def post(self) -> None:
        state.reset()
        self.json_ok({"ok": True})


def make_app() -> tornado.web.Application:
    return tornado.web.Application([
        (r"/auth/login", LoginHandler),
        (r"/auth/me", MeHandler),
        (r"/auth/password/forgot", ForgotPasswordHandler),
        (r"/auth/password/reset", ResetPasswordHandler),
        (r"/__test__/sent-reset-emails", SentEmailsHandler),
        (r"/__test__/reset-state", ResetStateHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8080, address="127.0.0.1")
    tornado.ioloop.IOLoop.current().start()
