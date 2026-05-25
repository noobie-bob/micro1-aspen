from __future__ import annotations

import json
import secrets
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=["*"],
        DATABASES={},
        INSTALLED_APPS=[],
        SECRET_KEY="aspen-test-secret-key-not-for-production",
        USE_TZ=False,
    )

from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt


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


def _json_error(status: int, detail: str) -> JsonResponse:
    return JsonResponse({"detail": detail}, status=status)


def _parse_json(request) -> Optional[dict]:
    try:
        return json.loads(request.body)
    except Exception:
        return None


def _bearer_token(request) -> Optional[str]:
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    return auth.removeprefix("Bearer ")


def _current_user(request):
    token = _bearer_token(request)
    if not token:
        return None
    email = state.sessions.get(token)
    if not email or email not in state.users:
        return None
    return state.users[email]


@csrf_exempt
def login(request):
    if request.method != "POST":
        return _json_error(405, "method not allowed")
    data = _parse_json(request)
    if not data or "email" not in data or "password" not in data:
        return _json_error(422, "missing fields")
    user = state.users.get(data["email"])
    if not user or user.password != data["password"]:
        return _json_error(401, "bad credentials")
    session_id = secrets.token_urlsafe(24)
    state.sessions[session_id] = user.email
    return JsonResponse({"access_token": session_id, "token_type": "bearer"})


@csrf_exempt
def me(request):
    user = _current_user(request)
    if not user:
        return _json_error(401, "invalid session")
    return JsonResponse({"email": user.email})


@csrf_exempt
def forgot_password(request):
    if request.method != "POST":
        return _json_error(405, "method not allowed")
    data = _parse_json(request)
    if not data or "email" not in data:
        return _json_error(422, "missing fields")
    user = state.users.get(data["email"])
    if not user:
        return JsonResponse({"ok": True, "message": "If the account exists, a reset link was sent."})
    token = secrets.token_urlsafe(24)
    user.reset_tokens.append(token)
    state.sent_reset_emails.append({"email": user.email, "token": token})
    return JsonResponse(
        {"ok": True, "message": "If the account exists, a reset link was sent."},
        status=202,
    )


@csrf_exempt
def reset_password(request):
    if request.method != "POST":
        return _json_error(405, "method not allowed")
    data = _parse_json(request)
    if not data or "token" not in data or "new_password" not in data:
        return _json_error(422, "missing fields")
    for user in state.users.values():
        if data["token"] in user.reset_tokens:
            user.password = data["new_password"]
            return JsonResponse({"ok": True})
    return _json_error(400, "invalid reset token")


@csrf_exempt
def sent_reset_emails_view(request):
    return JsonResponse({"emails": list(state.sent_reset_emails)})


@csrf_exempt
def reset_state_view(request):
    state.reset()
    return JsonResponse({"ok": True})


urlpatterns = [
    path("auth/login", login),
    path("auth/me", me),
    path("auth/password/forgot", forgot_password),
    path("auth/password/reset", reset_password),
    path("__test__/sent-reset-emails", sent_reset_emails_view),
    path("__test__/reset-state", reset_state_view),
]
