"""Bearer-token auth for taskhub.

Three static API keys are recognized:
    "admin-key" -> Caller(role="admin", user_id="admin-uuid")  # task authors
    "user-key"  -> Caller(role="user",  user_id="alice-uuid")  # participant alice
    "user2-key" -> Caller(role="user",  user_id="bob-uuid")    # participant bob
Any other token raises 401.

`Caller.is_admin` flags admins. `Caller.user_id` identifies the calling
participant.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, status

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


def caller(authorization: str | None = Header(default=None)) -> Caller:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization[len("Bearer ") :]
    entry = VALID_TOKENS.get(token)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    role, user_id = entry
    return Caller(role=role, user_id=user_id)
