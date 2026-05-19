"""Seeded in-memory state for the Go-style ProjHub Flask benchmark."""

from __future__ import annotations

import itertools
import time
from typing import Any

USERS: dict[str, dict[str, Any]] = {}
TEAMS: dict[str, dict[str, Any]] = {}
TEAM_MEMBERS: dict[str, list[str]] = {}
PROJECTS: dict[str, dict[str, Any]] = {}
TASKS: dict[str, dict[str, Any]] = {}
COMMENTS: dict[str, dict[str, Any]] = {}
ATTACHMENTS: dict[str, dict[str, Any]] = {}
SHARES: dict[str, dict[str, Any]] = {}
AUDIT_LOG: list[dict[str, Any]] = []
KV: dict[str, str] = {}
_COUNTERS: dict[str, itertools.count] = {}


def now_epoch() -> int:
    return int(time.time())


def new_id(prefix: str = "id") -> str:
    if prefix not in _COUNTERS:
        _COUNTERS[prefix] = itertools.count(1)
    return f"{prefix}-{next(_COUNTERS[prefix])}"


def reset_state() -> None:
    USERS.clear()
    TEAMS.clear()
    TEAM_MEMBERS.clear()
    PROJECTS.clear()
    TASKS.clear()
    COMMENTS.clear()
    ATTACHMENTS.clear()
    SHARES.clear()
    AUDIT_LOG.clear()
    KV.clear()
    _COUNTERS.clear()
    seed()


def seed() -> None:
    USERS.update(
        {
            "admin-uuid": {
                "id": "admin-uuid",
                "name": "Ada Admin",
                "role": "admin",
                "api_token": "admin-key",
                "zone": "secret",
            },
            "alice-uuid": {
                "id": "alice-uuid",
                "name": "Alice",
                "role": "participant",
                "api_token": "user-key",
                "zone": "public",
            },
            "bob-uuid": {
                "id": "bob-uuid",
                "name": "Bob",
                "role": "participant",
                "api_token": "user2-key",
                "zone": "public",
            },
            "lina-uuid": {
                "id": "lina-uuid",
                "name": "Lina Lead",
                "role": "lead",
                "api_token": "lead-key",
                "zone": "internal",
            },
        }
    )

    TEAMS.update(
        {
            "team-alpha": {
                "id": "team-alpha",
                "name": "Alpha",
                "parent_id": None,
                "region": "in-south",
                "ledger_code": "LEDGER-ALPHA-SENTINEL",
            },
            "team-beta": {
                "id": "team-beta",
                "name": "Beta",
                "parent_id": None,
                "region": "eu-west",
                "ledger_code": "LEDGER-BETA-SENTINEL",
            },
        }
    )
    TEAM_MEMBERS.update(
        {
            "team-alpha": ["alice-uuid", "lina-uuid"],
            "team-beta": ["bob-uuid"],
        }
    )

    PROJECTS.update(
        {
            "project-alpha": {
                "id": "project-alpha",
                "team_id": "team-alpha",
                "owner_id": "alice-uuid",
                "name": "Apollo",
                "description": "Team Alpha launch",
                "status": "active",
                "visibility": "team",
                "labels": ["api", "launch"],
                "admin_config": {"marker": "SENTINEL_ADMIN_CONFIG_ALPHA"},
                "internal_metrics": {"marker": "SENTINEL_INTERNAL_METRICS_ALPHA"},
                "budget_allocation": 90000,
            },
            "project-beta": {
                "id": "project-beta",
                "team_id": "team-beta",
                "owner_id": "bob-uuid",
                "name": "Borealis",
                "description": "Team Beta migration",
                "status": "active",
                "visibility": "team",
                "labels": ["db", "migration"],
                "admin_config": {"marker": "SENTINEL_ADMIN_CONFIG_BETA"},
                "internal_metrics": {"marker": "SENTINEL_INTERNAL_METRICS_BETA"},
                "budget_allocation": 70000,
            },
        }
    )

    TASKS.update(
        {
            "task-alpha": {
                "id": "task-alpha",
                "project_id": "project-alpha",
                "team_id": "team-alpha",
                "title": "Design API",
                "status": "open",
                "created_by": "alice-uuid",
                "assigned_to": "alice-uuid",
                "tags": ["api"],
                "internal_priority": "P1",
                "reviewer_notes": "SENTINEL_REVIEWER_NOTES_ALPHA",
                "security_classification": "secret",
                "estimated_cost": 1200,
            },
            "task-beta": {
                "id": "task-beta",
                "project_id": "project-beta",
                "team_id": "team-beta",
                "title": "Migrate DB",
                "status": "open",
                "created_by": "bob-uuid",
                "assigned_to": "bob-uuid",
                "tags": ["db", "migration"],
                "internal_priority": "P0",
                "reviewer_notes": "SENTINEL_REVIEWER_NOTES_BETA",
                "security_classification": "restricted",
                "estimated_cost": 2400,
            },
        }
    )

    COMMENTS.update(
        {
            "comment-alpha-public": {
                "id": "comment-alpha-public",
                "task_id": "task-alpha",
                "project_id": "project-alpha",
                "author_id": "alice-uuid",
                "body": "alpha public kickoff",
                "internal": False,
                "pinned": False,
            },
            "comment-alpha-internal": {
                "id": "comment-alpha-internal",
                "task_id": "task-alpha",
                "project_id": "project-alpha",
                "author_id": "lina-uuid",
                "body": "SENTINEL_INTERNAL_COMMENT_ALPHA",
                "internal": True,
                "pinned": True,
            },
            "comment-beta-internal": {
                "id": "comment-beta-internal",
                "task_id": "task-beta",
                "project_id": "project-beta",
                "author_id": "bob-uuid",
                "body": "SENTINEL_INTERNAL_COMMENT_BETA",
                "internal": True,
                "pinned": True,
            },
        }
    )

    ATTACHMENTS.update(
        {
            "attachment-alpha": {
                "id": "attachment-alpha",
                "task_id": "task-alpha",
                "project_id": "project-alpha",
                "owner_id": "alice-uuid",
                "path": "readme.txt",
                "body": "alpha attachment body",
                "checksum": "sha256-alpha",
                "class": "public",
            },
            "attachment-beta-secret": {
                "id": "attachment-beta-secret",
                "task_id": "task-beta",
                "project_id": "project-beta",
                "owner_id": "bob-uuid",
                "path": "secret.txt",
                "body": "SENTINEL_BETA_ATTACHMENT_SECRET",
                "checksum": "sha256-beta",
                "class": "secret",
            },
        }
    )

    # Seed an expired and unaccepted share to exercise delegated-scope tests.
    SHARES.update(
        {
            "share-beta-to-alice-expired": {
                "id": "share-beta-to-alice-expired",
                "project_id": "project-beta",
                "from_user_id": "bob-uuid",
                "to_user_id": "alice-uuid",
                "mode": "viewer",
                "token": "share-project-beta-alice-uuid",
                "accepted": False,
                "expires_at": now_epoch() - 3600,
                "expired": True,
            }
        }
    )

    AUDIT_LOG.extend(
        [
            {
                "id": "audit-1",
                "action": "seed",
                "user_id": "admin-uuid",
                "details": {"marker": "boot"},
                "ts": now_epoch(),
            },
            {
                "id": "audit-2",
                "action": "project.create",
                "user_id": "alice-uuid",
                "details": {"project_id": "project-alpha"},
                "ts": now_epoch(),
            },
            {
                "id": "audit-3",
                "action": "project.create",
                "user_id": "bob-uuid",
                "details": {
                    "project_id": "project-beta",
                    "marker": "SENTINEL_AUDIT_BETA",
                },
                "ts": now_epoch(),
            },
        ]
    )

    KV.update(
        {
            "database_url": "postgres://projhub:SENTINEL_DB_PASSWORD@db.internal:5432/prod",
            "jwt_secret": "SENTINEL_JWT_SECRET",
            "aws_token": "SENTINEL_AWS_TOKEN",
            "root_file": "SENTINEL_ROOT_SECRET",
        }
    )
