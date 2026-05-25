from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from litestar import Litestar, get, post, Request
from litestar.connection import Request  # noqa: F811
from litestar.exceptions import HTTPException
from litestar.response import Response
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class ResetRequest(BaseModel):
    email: str


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


@post("/auth/login")
async def login(data: LoginRequest) -> dict:
    user = state.users.get(data.email)
    if not user or user.password != data.password:
        raise HTTPException(status_code=401, detail="bad credentials")
    session_id = secrets.token_urlsafe(24)
    state.sessions[session_id] = user.email
    return {"access_token": session_id, "token_type": "bearer"}


@get("/auth/me")
async def me(request: Request) -> dict:
    user = _current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="invalid session")
    return {"email": user.email}


@post("/auth/password/forgot")
async def forgot_password(data: ResetRequest) -> Response:
    user = state.users.get(data.email)
    if not user:
        return Response(
            content={"ok": True, "message": "If the account exists, a reset link was sent."},
            status_code=200,
        )
    token = secrets.token_urlsafe(24)
    user.reset_tokens.append(token)
    state.sent_reset_emails.append({"email": user.email, "token": token})
    return Response(
        content={"ok": True, "message": "If the account exists, a reset link was sent."},
        status_code=202,
    )


@post("/auth/password/reset")
async def reset_password(data: ResetConfirmRequest) -> dict:
    for user in state.users.values():
        if data.token in user.reset_tokens:
            user.password = data.new_password
            return {"ok": True}
    raise HTTPException(status_code=400, detail="invalid reset token")


@get("/__test__/sent-reset-emails")
async def sent_reset_emails() -> dict:
    return {"emails": list(state.sent_reset_emails)}


@post("/__test__/reset-state")
async def reset_state_route() -> dict:
    state.reset()
    return {"ok": True}


app = Litestar(
    route_handlers=[
        login,
        me,
        forgot_password,
        reset_password,
        sent_reset_emails,
        reset_state_route,
    ],
)
