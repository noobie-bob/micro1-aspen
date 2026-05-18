"""ProjHub compact Flask API substrate for Aspen test-authoring.

Keep route behavior, auth, and object-scope logic in one readable application
file. Shared in-memory state lives in projhub.db so the existing conftest.py can
import reset_state exactly as written.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import traceback
from dataclasses import dataclass
from functools import wraps
from typing import Any

from flask import Flask, g, jsonify, request

from projhub.db import (
    AUDIT_LOG,
    PROJECTS,
    TASKS,
    TEAMS,
    TEAM_MEMBERS,
    new_id,
    reset_state,
)


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


def log_audit(action: str, user_id: str, details: dict[str, Any] | None = None) -> None:
    AUDIT_LOG.append(
        {
            "id": new_id(),
            "action": action,
            "user_id": user_id,
            "details": details or {},
        }
    )


def _extract_caller() -> tuple[Caller | None, tuple[str, int] | None]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, ("missing bearer token", 401)
    token = auth[len("Bearer ") :]
    entry = VALID_TOKENS.get(token)
    if entry is None:
        return None, ("invalid token", 401)
    role, user_id = entry
    return Caller(role=role, user_id=user_id), None


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        caller, error = _extract_caller()
        if error:
            return jsonify({"detail": error[0]}), error[1]
        g.caller = caller
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        caller, error = _extract_caller()
        if error:
            return jsonify({"detail": error[0]}), error[1]
        if not caller.is_admin:
            return jsonify({"detail": "admin required"}), 403
        g.caller = caller
        return fn(*args, **kwargs)

    return wrapper


def create_app() -> Flask:
    reset_state()
    app = Flask(__name__)
    app.config["TESTING"] = False

    # ------------------------------------------------------------------
    # Teams
    # ------------------------------------------------------------------

    @app.post("/teams")
    @require_admin
    def create_team():
        data = request.get_json(force=True)
        team_id = new_id()
        team = {
            "id": team_id,
            "name": data.get("name", "unnamed"),
            "internal_budget": data.get("internal_budget", 0),
            "admin_notes": data.get("admin_notes", ""),
            "billing_code": data.get("billing_code", ""),
            "created_by": g.caller.user_id,
        }
        TEAMS[team_id] = team
        TEAM_MEMBERS[team_id] = list(data.get("member_ids", []))
        log_audit("team_created", g.caller.user_id, {"team_id": team_id})
        return jsonify(team)

    @app.get("/teams")
    @require_auth
    def list_teams():
        return jsonify(list(TEAMS.values()))

    @app.get("/teams/<team_id>")
    @require_auth
    def get_team(team_id: str):
        team = TEAMS.get(team_id)
        if team is None:
            return jsonify({"detail": "team not found"}), 404
        body = dict(team)
        body["members"] = TEAM_MEMBERS.get(team_id, [])
        return jsonify(body)

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    @app.post("/projects")
    @require_auth
    def create_project():
        data = request.get_json(force=True)
        team_id = data.get("team_id")
        if not team_id or team_id not in TEAMS:
            return jsonify({"detail": "valid team_id required"}), 400
        if not g.caller.is_admin and g.caller.user_id not in TEAM_MEMBERS.get(
            team_id, []
        ):
            return jsonify({"detail": "not a member of this team"}), 403

        project_id = new_id()
        project = {
            "id": project_id,
            "name": data.get("name", "unnamed"),
            "description": data.get("description", ""),
            "team_id": team_id,
            "owner_id": g.caller.user_id,
            "status": data.get("status", "active"),
            "admin_config": data.get(
                "admin_config", {"tier": "standard", "auto_review": False}
            ),
            "internal_metrics": data.get(
                "internal_metrics", {"risk": "low", "velocity": 0}
            ),
            "budget_allocation": data.get("budget_allocation", 0),
        }
        PROJECTS[project_id] = project
        log_audit("project_created", g.caller.user_id, {"project_id": project_id})
        return jsonify(project)

    @app.get("/projects")
    @require_auth
    def list_projects():
        return jsonify(list(PROJECTS.values()))

    @app.get("/projects/<project_id>")
    @require_auth
    def get_project(project_id: str):
        project = PROJECTS.get(project_id)
        if project is None:
            return jsonify({"detail": "project not found"}), 404
        return jsonify(project)

    @app.patch("/projects/<project_id>")
    @require_auth
    def update_project(project_id: str):
        project = PROJECTS.get(project_id)
        if project is None:
            return jsonify({"detail": "project not found"}), 404
        data = request.get_json(force=True)
        for key in (
            "name",
            "description",
            "status",
            "admin_config",
            "internal_metrics",
            "budget_allocation",
        ):
            if key in data:
                project[key] = data[key]
        log_audit("project_updated", g.caller.user_id, {"project_id": project_id})
        return jsonify(project)

    @app.post("/projects/<project_id>/share")
    @require_auth
    def share_project(project_id: str):
        project = PROJECTS.get(project_id)
        if project is None:
            return jsonify({"detail": "project not found"}), 404
        return jsonify(
            {
                "project_id": project_id,
                "share_id": new_id(),
                "url": f"/shared/{project_id}",
                "name": project.get("name"),
                "config": project.get("admin_config"),
                "metrics": project.get("internal_metrics"),
                "budget": project.get("budget_allocation"),
            }
        )

    @app.get("/projects/<project_id>/export")
    @require_auth
    def export_project(project_id: str):
        project = PROJECTS.get(project_id)
        if project is None:
            return jsonify({"detail": "project not found"}), 404
        return jsonify(project)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    @app.post("/projects/<project_id>/tasks")
    @require_auth
    def create_task(project_id: str):
        project = PROJECTS.get(project_id)
        if project is None:
            return jsonify({"detail": "project not found"}), 404
        if not g.caller.is_admin and g.caller.user_id not in TEAM_MEMBERS.get(
            project.get("team_id"), []
        ):
            return jsonify({"detail": "not a member of this team"}), 403

        data = request.get_json(force=True)
        task_id = new_id()
        task = {
            "id": task_id,
            "project_id": project_id,
            "team_id": project.get("team_id"),
            "title": data.get("title", "untitled"),
            "description": data.get("description", ""),
            "status": data.get("status", "open"),
            "assigned_to": data.get("assigned_to"),
            "created_by": g.caller.user_id,
            "internal_priority": data.get("internal_priority", "P2"),
            "reviewer_notes": data.get("reviewer_notes", ""),
        }
        TASKS[task_id] = task
        log_audit("task_created", g.caller.user_id, {"task_id": task_id})
        return jsonify(task)

    @app.get("/projects/<project_id>/tasks")
    @require_auth
    def list_project_tasks(project_id: str):
        if project_id not in PROJECTS:
            return jsonify({"detail": "project not found"}), 404
        return jsonify([t for t in TASKS.values() if t.get("project_id") == project_id])

    @app.get("/tasks/<task_id>")
    @require_auth
    def get_task(task_id: str):
        task = TASKS.get(task_id)
        if task is None:
            return jsonify({"detail": "task not found"}), 404
        return jsonify(task)

    @app.patch("/tasks/<task_id>")
    @require_auth
    def update_task(task_id: str):
        task = TASKS.get(task_id)
        if task is None:
            return jsonify({"detail": "task not found"}), 404
        data = request.get_json(force=True)
        for key in (
            "title",
            "description",
            "status",
            "assigned_to",
            "internal_priority",
            "reviewer_notes",
        ):
            if key in data:
                task[key] = data[key]
        log_audit("task_updated", g.caller.user_id, {"task_id": task_id})
        return jsonify(task)

    @app.post("/tasks/<task_id>/assign")
    @require_auth
    def assign_task(task_id: str):
        task = TASKS.get(task_id)
        if task is None:
            return jsonify({"detail": "task not found"}), 404
        data = request.get_json(force=True)
        if not data.get("user_id"):
            return jsonify({"detail": "user_id required"}), 400
        task["assigned_to"] = data["user_id"]
        log_audit(
            "task_assigned",
            g.caller.user_id,
            {"task_id": task_id, "assigned_to": data["user_id"]},
        )
        return jsonify(task)

    @app.post("/tasks/<task_id>/transition")
    @require_auth
    def transition_task(task_id: str):
        task = TASKS.get(task_id)
        if task is None:
            return jsonify({"detail": "task not found"}), 404
        data = request.get_json(force=True)
        status = data.get("status")
        if status not in {"open", "in_progress", "review", "done", "closed", "deleted"}:
            return jsonify({"detail": "invalid status"}), 400
        task["status"] = status
        log_audit(
            "task_transitioned",
            g.caller.user_id,
            {"task_id": task_id, "status": status},
        )
        return jsonify(task)

    # ------------------------------------------------------------------
    # Search and diagnostics
    # ------------------------------------------------------------------

    @app.get("/search/projects")
    @require_auth
    def search_projects():
        q = request.args.get("q", "")
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        db.execute(
            "CREATE TABLE project_index (id TEXT, name TEXT, description TEXT, team_id TEXT, admin_config TEXT)"
        )
        for p in PROJECTS.values():
            db.execute(
                "INSERT INTO project_index VALUES (?, ?, ?, ?, ?)",
                (
                    p["id"],
                    p.get("name", ""),
                    p.get("description", ""),
                    p.get("team_id", ""),
                    str(p.get("admin_config", "")),
                ),
            )
        db.commit()
        sql = f"SELECT id, name, description, team_id, admin_config FROM project_index WHERE name LIKE '%{q}%'"
        try:
            rows = [dict(row) for row in db.execute(sql).fetchall()]
        except Exception as exc:
            return jsonify({"detail": f"search error: {exc}"}), 400
        finally:
            db.close()
        return jsonify(rows)

    @app.get("/debug/users")
    def debug_users():
        return jsonify(
            [
                {"user_id": user_id, "role": role, "api_token": token}
                for token, (role, user_id) in VALID_TOKENS.items()
            ]
        )

    @app.get("/debug/env")
    def debug_env():
        return jsonify(dict(os.environ))

    @app.get("/debug/config")
    def debug_config():
        return jsonify(
            {
                "python_version": sys.version,
                "python_path": sys.path,
                "working_directory": os.getcwd(),
                "platform": sys.platform,
                "pid": os.getpid(),
            }
        )

    @app.get("/debug/error")
    def debug_error():
        try:
            1 / 0
        except Exception:
            return jsonify(
                {
                    "error": "internal server error",
                    "traceback": traceback.format_exc(),
                    "cwd": os.getcwd(),
                    "python_version": sys.version,
                }
            ), 500

    @app.errorhandler(Exception)
    def handle_exception(exc):
        return jsonify(
            {
                "error": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            }
        ), 500

    @app.errorhandler(404)
    def handle_404(exc):
        return jsonify({"error": "not found"}), 404

    return app


app = create_app()
