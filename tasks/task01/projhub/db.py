"""In-memory storage for the ProjHub demo service.

Real project-management platforms use Postgres + blob storage. For the sample
task we keep the storage shape (teams, projects, tasks, comments, attachments)
but replace the backing store with in-process dicts + a temp directory so the
service is runnable inside a small Docker image with no external deps.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any

# ── Core tables ──────────────────────────────────────────────────────────────
TEAMS: dict[str, dict[str, Any]] = {}
TEAM_MEMBERS: dict[str, list[str]] = {}          # team_id -> [user_id, ...]
PROJECTS: dict[str, dict[str, Any]] = {}
TASKS: dict[str, dict[str, Any]] = {}
COMMENTS: dict[str, list[dict[str, Any]]] = {}   # task_id -> [comment, ...]
AUDIT_LOG: list[dict[str, Any]] = []

# ── File-system roots ────────────────────────────────────────────────────────
ATTACHMENT_ROOT: str = ""


def reset_state() -> None:
    """Wipe and re-create all storage. Called at app startup and from tests."""
    global ATTACHMENT_ROOT
    TEAMS.clear()
    TEAM_MEMBERS.clear()
    PROJECTS.clear()
    TASKS.clear()
    COMMENTS.clear()
    AUDIT_LOG.clear()
    if ATTACHMENT_ROOT and os.path.isdir(ATTACHMENT_ROOT):
        shutil.rmtree(ATTACHMENT_ROOT, ignore_errors=True)
    ATTACHMENT_ROOT = tempfile.mkdtemp(prefix="projhub-attachments-")


def new_id() -> str:
    return uuid.uuid4().hex


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def attachment_dir(task_id: str) -> str:
    path = os.path.join(ATTACHMENT_ROOT, task_id)
    os.makedirs(path, exist_ok=True)
    return path


def get_user_team_ids(user_id: str) -> list[str]:
    """Return list of team_ids the user belongs to."""
    return [tid for tid, members in TEAM_MEMBERS.items() if user_id in members]


def log_audit(action: str, user_id: str, details: dict | None = None) -> None:
    AUDIT_LOG.append({
        "id": new_id(),
        "action": action,
        "user_id": user_id,
        "details": details or {},
        "timestamp": now_iso(),
    })
