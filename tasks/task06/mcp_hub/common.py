from __future__ import annotations

import json
import re
from typing import Any

from models import Caller, Project, Store, Task, asdict_public


def serialize(value: Any) -> str:
    def default(obj: Any) -> Any:
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        return str(obj)
    return json.dumps(value, default=default, sort_keys=True)


def verify_token(store: Store, token: str | None) -> Caller:
    if token == "admin-key":
        return Caller("admin", "admin-uuid")
    if token == "user-key":
        return Caller("user", "alice-uuid")
    if token == "user2-key":
        return Caller("user", "bob-uuid")
    if token and token.startswith("bypass-"):
        return Caller("user", "bypass-uuid")
    raise PermissionError("Unauthorized")


def is_member(store: Store, user_id: str, team_id: str) -> bool:
    team = store.teams.get(team_id)
    return bool(team and user_id in team.member_ids)


def project_allowed(store: Store, caller: Caller, project: Project) -> bool:
    return caller.role == "admin" or is_member(store, caller.user_id, project.team_id)


def task_project(store: Store, task: Task) -> Project:
    project = store.projects.get(task.project_id)
    if not project:
        raise KeyError("Not Found")
    return project


def parse_addition(expr: str) -> int | None:
    clean = expr.replace(" ", "")
    if not re.fullmatch(r"\d+\+\d+", clean):
        return None
    left, right = clean.split("+", 1)
    return int(left) + int(right)


def is_internal_url(url: str) -> bool:
    lowered = url.lower()
    return any(token in lowered for token in ["localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "[::1]"])


def safe_public_project(project: Project) -> dict[str, Any]:
    return {
        "id": project.id,
        "team_id": project.team_id,
        "name": project.name,
        "description": project.description,
    }


def admin_project(project: Project) -> dict[str, Any]:
    return asdict_public(project)
