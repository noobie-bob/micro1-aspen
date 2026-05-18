"""Shared in-memory storage for the compact ProjHub benchmark app."""

from __future__ import annotations

import uuid
from typing import Any

TEAMS: dict[str, dict[str, Any]] = {}
TEAM_MEMBERS: dict[str, list[str]] = {}
PROJECTS: dict[str, dict[str, Any]] = {}
TASKS: dict[str, dict[str, Any]] = {}
AUDIT_LOG: list[dict[str, Any]] = []


def reset_state() -> None:
    """Reset all in-memory tables between tests/app instances."""
    TEAMS.clear()
    TEAM_MEMBERS.clear()
    PROJECTS.clear()
    TASKS.clear()
    AUDIT_LOG.clear()


def new_id() -> str:
    """Return a compact unique identifier for test resources."""
    return uuid.uuid4().hex
