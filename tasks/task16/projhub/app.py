from __future__ import annotations

import json
import secrets
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import falcon


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


def _bearer_token(req: falcon.Request) -> Optional[str]:
    auth = req.get_header("Authorization") or ""
    if not auth.startswith("Bearer "):
        return None
    return auth[7:]


def _current_user(req: falcon.Request) -> Optional[User]:
    token = _bearer_token(req)
    if not token:
        return None
    email = state.sessions.get(token)
    if not email or email not in state.users:
        return None
    return state.users[email]


class LoginResource:
    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            data = req.get_media()
        except Exception:
            resp.status = falcon.HTTP_422
            resp.media = {"detail": "invalid json"}
            return
        if not data or "email" not in data or "password" not in data:
            resp.status = falcon.HTTP_422
            resp.media = {"detail": "missing fields"}
            return
        user = state.users.get(data["email"])
        if not user or user.password != data["password"]:
            resp.status = falcon.HTTP_401
            resp.media = {"detail": "bad credentials"}
            return
        session_id = secrets.token_urlsafe(24)
        state.sessions[session_id] = user.email
        resp.media = {"access_token": session_id, "token_type": "bearer"}


class MeResource:
    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        user = _current_user(req)
        if not user:
            resp.status = falcon.HTTP_401
            resp.media = {"detail": "invalid session"}
            return
        resp.media = {"email": user.email}


class ForgotPasswordResource:
    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            data = req.get_media()
        except Exception:
            resp.status = falcon.HTTP_422
            resp.media = {"detail": "invalid json"}
            return
        if not data or "email" not in data:
            resp.status = falcon.HTTP_422
            resp.media = {"detail": "missing fields"}
            return
        user = state.users.get(data["email"])
        if not user:
            resp.media = {"ok": True, "message": "If the account exists, a reset link was sent."}
            return
        token = secrets.token_urlsafe(24)
        user.reset_tokens.append(token)
        state.sent_reset_emails.append({"email": user.email, "token": token})
        resp.status = falcon.HTTP_202
        resp.media = {"ok": True, "message": "If the account exists, a reset link was sent."}


class ResetPasswordResource:
    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            data = req.get_media()
        except Exception:
            resp.status = falcon.HTTP_422
            resp.media = {"detail": "invalid json"}
            return
        if not data or "token" not in data or "new_password" not in data:
            resp.status = falcon.HTTP_422
            resp.media = {"detail": "missing fields"}
            return
        for user in state.users.values():
            if data["token"] in user.reset_tokens:
                user.password = data["new_password"]
                resp.media = {"ok": True}
                return
        resp.status = falcon.HTTP_400
        resp.media = {"detail": "invalid reset token"}


class SentEmailsResource:
    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = {"emails": list(state.sent_reset_emails)}


class ResetStateResource:
    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        state.reset()
        resp.media = {"ok": True}


application = falcon.App()
application.add_route("/auth/login", LoginResource())
application.add_route("/auth/me", MeResource())
application.add_route("/auth/password/forgot", ForgotPasswordResource())
application.add_route("/auth/password/reset", ResetPasswordResource())
application.add_route("/__test__/sent-reset-emails", SentEmailsResource())
application.add_route("/__test__/reset-state", ResetStateResource())
