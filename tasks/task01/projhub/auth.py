"""Bearer-token auth for ProjHub.

Three static API keys are recognized:
    "admin-key" -> Caller(role="admin", user_id="admin-uuid")   # org admin
    "user-key"  -> Caller(role="user",  user_id="alice-uuid")   # participant alice
    "user2-key" -> Caller(role="user",  user_id="bob-uuid")     # participant bob
Any other token raises 401.

`Caller.is_admin` flags admins. `Caller.user_id` identifies the calling
participant. Team membership is tracked in the database, not in the token.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps

from flask import g, jsonify, request

VALID_TOKENS: dict[str, tuple[str, str]] = {
    "admin-key": ("admin", "admin-uuid"),
    "user-key": ("user", "alice-uuid"),
    "user2-key": ("user", "bob-uuid"),
}


@dataclass(frozen=True)
class Caller:
    role: str
    user_id: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def _extract_caller():
    """Parse the Authorization header and return (Caller, None) or (None, error_tuple)."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, ("missing bearer token", 401)
    token = auth[len("Bearer "):]
    entry = VALID_TOKENS.get(token)
    if entry is None:
        return None, ("invalid token", 401)
    role, user_id = entry
    return Caller(role=role, user_id=user_id), None


def require_auth(f):
    """Decorator: any authenticated caller."""
    @wraps(f)
    def decorated(*args, **kwargs):
        caller, error = _extract_caller()
        if error:
            return jsonify({"detail": error[0]}), error[1]
        g.caller = caller
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decorator: admin-only endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        caller, error = _extract_caller()
        if error:
            return jsonify({"detail": error[0]}), error[1]
        if not caller.is_admin:
            return jsonify({"detail": "admin required"}), 403
        g.caller = caller
        return f(*args, **kwargs)
    return decorated
