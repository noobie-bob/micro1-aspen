"""ProjHub Flask benchmark app, shaped like the successful Go substrate.

Design goals (for test-authoring calibration):
- Seeded multi-team data with sentinel markers
- Central project/task gate helpers (readable access model)
- Central serializers (response shaping is explicit)
- Primary, secondary/package, discovery, operational, and unsafe-input surfaces
- A mix of secure expectations and intentionally unsafe behaviors for tests to detect

This is a benchmark substrate, not production code.
"""

from __future__ import annotations

import base64
import os
import sys
import traceback
from dataclasses import dataclass
from functools import wraps
from typing import Any

from flask import Flask, g, jsonify, request

from projhub.db import (
    ATTACHMENTS,
    AUDIT_LOG,
    COMMENTS,
    KV,
    PROJECTS,
    SHARES,
    TASKS,
    TEAMS,
    TEAM_MEMBERS,
    USERS,
    now_epoch,
    new_id,
    reset_state,
)


# Bearer-token auth: compatible with existing pytest fixtures.
VALID_TOKENS: dict[str, tuple[str, str]] = {
    "admin-key": ("admin", "admin-uuid"),
    "user-key": ("participant", "alice-uuid"),
    "user2-key": ("participant", "bob-uuid"),
    "lead-key": ("lead", "lina-uuid"),
}


@dataclass(frozen=True)
class Caller:
    role: str
    user_id: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_lead(self) -> bool:
        return self.role == "lead"


@dataclass
class Gate:
    ok: bool
    via: str = ""
    reason: str = "forbidden"
    project: dict[str, Any] | None = None
    task: dict[str, Any] | None = None
    team_id: str | None = None


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


def log_audit(action: str, user_id: str, details: dict[str, Any] | None = None) -> None:
    AUDIT_LOG.append(
        {
            "id": new_id("audit"),
            "action": action,
            "user_id": user_id,
            "details": details or {},
            "ts": now_epoch(),
        }
    )


def caller_team_ids(caller: Caller) -> list[str]:
    return [tid for tid, members in TEAM_MEMBERS.items() if caller.user_id in members]


def share_valid_for(caller: Caller, project_id: str) -> tuple[bool, str]:
    """Return (valid, via) for a share grant."""
    now = now_epoch()
    for sh in SHARES.values():
        if sh.get("project_id") != project_id:
            continue
        if sh.get("to_user_id") != caller.user_id:
            continue
        if not sh.get("accepted"):
            continue
        if sh.get("expires_at", 0) and now > int(sh.get("expires_at", 0)):
            continue
        if sh.get("expired"):
            continue
        return True, "share"
    return False, ""


def project_gate(caller: Caller, project_id: str) -> Gate:
    project = PROJECTS.get(project_id)
    if project is None:
        return Gate(False, reason="missing")
    team_id = project.get("team_id")
    if caller.is_admin:
        return Gate(True, via="admin", project=project, team_id=team_id)
    if caller.is_lead and team_id in caller_team_ids(caller):
        return Gate(True, via="lead", project=project, team_id=team_id)
    if team_id in caller_team_ids(caller):
        return Gate(True, via="team", project=project, team_id=team_id)
    valid, via = share_valid_for(caller, project_id)
    if valid:
        return Gate(True, via=via, project=project, team_id=team_id)
    return Gate(False, reason="forbidden", project=project, team_id=team_id)


def task_gate(caller: Caller, task_id: str) -> Gate:
    task = TASKS.get(task_id)
    if task is None:
        return Gate(False, reason="missing")
    pg = project_gate(caller, task.get("project_id"))
    pg.task = task
    if pg.ok:
        return pg
    if (
        task.get("created_by") == caller.user_id
        or task.get("assigned_to") == caller.user_id
    ):
        pg.ok = True
        pg.via = "task-person"
        return pg
    return pg


def hidden_status(gate: Gate) -> int:
    return 404 if gate.reason == "missing" else 403


def project_view(project: dict[str, Any], caller: Caller, via: str) -> dict[str, Any]:
    """Public-ish project view, with privileged fields conditionally included."""
    body = {
        "id": project["id"],
        "team_id": project["team_id"],
        "owner_id": project.get("owner_id"),
        "name": project.get("name"),
        "description": project.get("description", ""),
        "status": project.get("status", "active"),
        "visibility": project.get("visibility", "team"),
        "labels": project.get("labels", []),
    }
    if caller.is_admin or caller.is_lead or via in {"admin", "lead"}:
        body["admin_config"] = project.get("admin_config")
        body["internal_metrics"] = project.get("internal_metrics")
        body["budget_allocation"] = project.get("budget_allocation")
    return body


def task_view(task: dict[str, Any], caller: Caller, via: str) -> dict[str, Any]:
    """Public-ish task view, with privileged fields conditionally included."""
    body = {
        "id": task["id"],
        "project_id": task["project_id"],
        "team_id": task["team_id"],
        "title": task.get("title"),
        "status": task.get("status", "open"),
        "assigned_to": task.get("assigned_to"),
        "created_by": task.get("created_by"),
        "tags": task.get("tags", []),
    }
    if caller.is_admin or caller.is_lead or via in {"admin", "lead"}:
        body["internal_priority"] = task.get("internal_priority")
        body["reviewer_notes"] = task.get("reviewer_notes")
        body["security_classification"] = task.get("security_classification")
        body["estimated_cost"] = task.get("estimated_cost")
    return body


def create_app() -> Flask:
    reset_state()
    app = Flask(__name__)
    app.config["TESTING"] = False

    # ------------------------
    # Health and identity
    # ------------------------

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    @app.get("/me")
    @require_auth
    def me():
        user = dict(
            USERS.get(g.caller.user_id, {"id": g.caller.user_id, "role": g.caller.role})
        )
        user.pop("api_token", None)
        return jsonify(user)

    # ------------------------
    # Teams
    # ------------------------

    @app.post("/teams")
    @require_admin
    def create_team():
        data = request.get_json(force=True)
        team_id = data.get("id") or new_id("team")
        team = {
            "id": team_id,
            "name": data.get("name", "unnamed"),
            "parent_id": data.get("parent_id"),
            "region": data.get("region", "local"),
            "ledger_code": data.get("billing_code") or data.get("ledger_code", ""),
            "internal_budget": data.get("internal_budget", 0),
            "admin_notes": data.get("admin_notes", ""),
            "created_by": g.caller.user_id,
        }
        TEAMS[team_id] = team
        TEAM_MEMBERS[team_id] = list(data.get("member_ids", []))
        log_audit("team.create", g.caller.user_id, {"team_id": team_id})
        return jsonify(team)

    @app.get("/teams")
    @require_auth
    def list_teams():
        if g.caller.is_admin:
            return jsonify(list(TEAMS.values()))
        allowed = set(caller_team_ids(g.caller))
        return jsonify([t for t in TEAMS.values() if t["id"] in allowed])

    @app.get("/teams/<team_id>")
    @require_auth
    def get_team(team_id: str):
        team = TEAMS.get(team_id)
        if team is None:
            return jsonify({"detail": "team not found"}), 404
        if not g.caller.is_admin and team_id not in caller_team_ids(g.caller):
            return jsonify({"detail": "team not found"}), 404
        body = dict(team)
        if g.caller.is_admin:
            body["members"] = TEAM_MEMBERS.get(team_id, [])
        return jsonify(body)

    # ------------------------
    # Projects (primary)
    # ------------------------

    @app.post("/projects")
    @require_auth
    def create_project():
        data = request.get_json(force=True)
        team_id = data.get("team_id")
        if not team_id or team_id not in TEAMS:
            return jsonify({"detail": "valid team_id required"}), 400
        if not g.caller.is_admin and team_id not in caller_team_ids(g.caller):
            return jsonify({"detail": "not a member of this team"}), 403
        project_id = data.get("id") or new_id("project")
        project = {
            "id": project_id,
            "team_id": team_id,
            "owner_id": data.get("owner_id", g.caller.user_id),
            "name": data.get("name", "unnamed"),
            "description": data.get("description", ""),
            "status": data.get("status", "active"),
            "visibility": data.get("visibility", "team"),
            "labels": data.get("labels", []),
            "admin_config": data.get(
                "admin_config", {"marker": "default-admin-config"}
            ),
            "internal_metrics": data.get(
                "internal_metrics", {"marker": "default-internal-metrics"}
            ),
            "budget_allocation": data.get("budget_allocation", 0),
        }
        PROJECTS[project_id] = project
        log_audit("project.create", g.caller.user_id, {"project_id": project_id})
        return jsonify(
            project_view(project, g.caller, "admin" if g.caller.is_admin else "team")
        ), 201

    @app.get("/projects")
    @require_auth
    def list_projects():
        q = request.args.get("q", "")
        include = request.args.get("include", "")
        rows: list[dict[str, Any]] = []
        for project in PROJECTS.values():
            gate = project_gate(g.caller, project["id"])
            # Intentional widened-discovery paths (for tests).
            widened = (
                include == "all" or q.lower().startswith("a") or " or " in q.lower()
            )
            if gate.ok or widened:
                rows.append(project_view(project, g.caller, gate.via))
        return jsonify(rows)

    @app.get("/projects/<project_id>")
    @require_auth
    def get_project(project_id: str):
        gate = project_gate(g.caller, project_id)
        if not gate.ok:
            return jsonify({"detail": "project not found"}), hidden_status(gate)
        return jsonify(project_view(gate.project, g.caller, gate.via))

    @app.patch("/projects/<project_id>")
    @require_auth
    def patch_project(project_id: str):
        gate = project_gate(g.caller, project_id)
        if not gate.ok:
            return jsonify({"detail": "forbidden"}), 403
        data = request.get_json(force=True)
        project = gate.project
        # Intentional mass-assignment style flaw.
        for key in (
            "name",
            "description",
            "status",
            "team_id",
            "owner_id",
            "admin_config",
            "internal_metrics",
            "budget_allocation",
        ):
            if key in data:
                project[key] = data[key]
        log_audit("project.patch", g.caller.user_id, {"project_id": project_id})
        return jsonify(project_view(project, g.caller, gate.via))

    @app.delete("/projects/<project_id>")
    @require_auth
    def delete_project(project_id: str):
        gate = project_gate(g.caller, project_id)
        if not gate.ok or not (
            g.caller.is_admin or gate.project.get("owner_id") == g.caller.user_id
        ):
            return jsonify({"detail": "forbidden"}), 403
        PROJECTS.pop(project_id, None)
        log_audit("project.delete", g.caller.user_id, {"project_id": project_id})
        return "", 204

    # ------------------------
    # Tasks (primary)
    # ------------------------

    @app.post("/projects/<project_id>/tasks")
    @require_auth
    def create_task(project_id: str):
        gate = project_gate(g.caller, project_id)
        if not gate.ok:
            return jsonify({"detail": "forbidden"}), 403
        data = request.get_json(force=True)
        task_id = data.get("id") or new_id("task")
        task = {
            "id": task_id,
            "project_id": project_id,
            "team_id": gate.project["team_id"],
            "title": data.get("title", "untitled"),
            "status": data.get("status", "open"),
            "created_by": data.get("created_by", g.caller.user_id),
            "assigned_to": data.get("assigned_to", g.caller.user_id),
            "tags": data.get("tags", []),
            "internal_priority": data.get("internal_priority", "P2"),
            "reviewer_notes": data.get("reviewer_notes", ""),
            "security_classification": data.get("security_classification", "public"),
            "estimated_cost": data.get("estimated_cost", 0),
        }
        TASKS[task_id] = task
        log_audit(
            "task.create",
            g.caller.user_id,
            {"project_id": project_id, "task_id": task_id},
        )
        return jsonify(task_view(task, g.caller, gate.via)), 201

    @app.get("/projects/<project_id>/tasks")
    @require_auth
    def list_project_tasks(project_id: str):
        gate = project_gate(g.caller, project_id)
        if not gate.ok:
            return jsonify({"detail": "project not found"}), hidden_status(gate)
        rollup = request.args.get("rollup") == "tree"
        rows = []
        for task in TASKS.values():
            if task.get("project_id") == project_id or (
                rollup and task.get("team_id") == gate.team_id
            ):
                rows.append(task_view(task, g.caller, gate.via))
        return jsonify(rows)

    @app.get("/tasks/<task_id>")
    @require_auth
    def get_task(task_id: str):
        gate = task_gate(g.caller, task_id)
        if not gate.ok:
            return jsonify({"detail": "task not found"}), hidden_status(gate)
        return jsonify(task_view(gate.task, g.caller, gate.via))

    @app.patch("/tasks/<task_id>")
    @require_auth
    def patch_task(task_id: str):
        gate = task_gate(g.caller, task_id)
        if not gate.ok:
            return jsonify({"detail": "forbidden"}), 403
        data = request.get_json(force=True)
        task = gate.task
        for key in (
            "title",
            "status",
            "project_id",
            "team_id",
            "created_by",
            "assigned_to",
            "internal_priority",
            "reviewer_notes",
            "security_classification",
            "estimated_cost",
        ):
            if key in data:
                task[key] = data[key]
        log_audit("task.patch", g.caller.user_id, {"task_id": task_id})
        return jsonify(task_view(task, g.caller, gate.via))

    @app.delete("/tasks/<task_id>")
    @require_auth
    def delete_task(task_id: str):
        gate = task_gate(g.caller, task_id)
        if not gate.ok:
            return jsonify({"detail": "forbidden"}), 403
        TASKS.pop(task_id, None)
        log_audit("task.delete", g.caller.user_id, {"task_id": task_id})
        return "", 204

    @app.post("/tasks/<task_id>/assign")
    @require_auth
    def assign_task(task_id: str):
        gate = task_gate(g.caller, task_id)
        if not gate.ok:
            return jsonify({"detail": "forbidden"}), 403
        data = request.get_json(force=True)
        if not data.get("user_id"):
            return jsonify({"detail": "user_id required"}), 400
        gate.task["assigned_to"] = data["user_id"]
        log_audit(
            "task.assign",
            g.caller.user_id,
            {"task_id": task_id, "assigned_to": data["user_id"]},
        )
        return jsonify(task_view(gate.task, g.caller, gate.via))

    @app.post("/tasks/<task_id>/transition")
    @require_auth
    def transition_task(task_id: str):
        gate = task_gate(g.caller, task_id)
        if not gate.ok:
            return jsonify({"detail": "forbidden"}), 403
        data = request.get_json(force=True)
        status = data.get("status")
        if status not in {"open", "in_progress", "review", "done", "closed", "deleted"}:
            return jsonify({"detail": "invalid status"}), 400
        gate.task["status"] = status
        log_audit(
            "task.transition", g.caller.user_id, {"task_id": task_id, "status": status}
        )
        return jsonify(task_view(gate.task, g.caller, gate.via))

    # ------------------------
    # Delegated access (shares)
    # ------------------------

    @app.post("/projects/<project_id>/shares")
    @require_auth
    def create_share(project_id: str):
        gate = project_gate(g.caller, project_id)
        if not gate.ok:
            return jsonify({"detail": "forbidden"}), 403
        data = request.get_json(force=True)
        share_id = new_id("share")
        ttl_hours = int(data.get("ttl_hours", 24))
        expires_at = now_epoch() + ttl_hours * 3600
        share = {
            "id": share_id,
            "project_id": project_id,
            "from_user_id": g.caller.user_id,
            "to_user_id": data.get("user_id"),
            "mode": data.get("mode", "viewer"),
            "token": f"share-{project_id}-{data.get('user_id')}",
            "expires_at": expires_at,
            "accepted": bool(data.get("accepted", False)),
        }
        SHARES[share_id] = share
        log_audit(
            "share.create",
            g.caller.user_id,
            {"share_id": share_id, "project_id": project_id},
        )
        return jsonify(share), 201

    @app.post("/shares/<share_id>/accept")
    @require_auth
    def accept_share(share_id: str):
        share = SHARES.get(share_id)
        if share is None:
            return jsonify({"detail": "share not found"}), 404
        data = request.get_json(force=True) if request.is_json else {}
        token = data.get("token")
        # Accept if caller is target OR provides token.
        if share.get("to_user_id") != g.caller.user_id and token != share.get("token"):
            return jsonify({"detail": "forbidden"}), 403
        share["accepted"] = True
        log_audit("share.accept", g.caller.user_id, {"share_id": share_id})
        return jsonify(share)

    # ------------------------
    # Comments and attachments
    # ------------------------

    @app.post("/tasks/<task_id>/comments")
    @require_auth
    def add_comment(task_id: str):
        gate = task_gate(g.caller, task_id)
        if not gate.ok:
            return jsonify({"detail": "forbidden"}), 403
        data = request.get_json(force=True)
        comment_id = new_id("comment")
        comment = {
            "id": comment_id,
            "task_id": task_id,
            "project_id": gate.task["project_id"],
            "author_id": g.caller.user_id,
            "body": data.get("body", ""),
            "internal": bool(data.get("internal", False)),
            "pinned": bool(data.get("pinned", False)),
        }
        COMMENTS[comment_id] = comment
        return jsonify(comment), 201

    @app.get("/tasks/<task_id>/comments")
    @require_auth
    def list_comments(task_id: str):
        gate = task_gate(g.caller, task_id)
        if not gate.ok:
            return jsonify({"detail": "task not found"}), hidden_status(gate)
        rows = []
        for comment in COMMENTS.values():
            if comment["task_id"] == task_id:
                # Intentional pinned/internal leak.
                if (
                    not comment.get("internal")
                    or g.caller.is_admin
                    or g.caller.is_lead
                    or comment.get("pinned")
                ):
                    rows.append(comment)
        return jsonify(rows)

    @app.post("/tasks/<task_id>/attachments")
    @require_auth
    def upload_attachment(task_id: str):
        gate = task_gate(g.caller, task_id)
        if not gate.ok:
            return jsonify({"detail": "forbidden"}), 403
        data = request.get_json(force=True)
        attachment_id = new_id("attachment")
        raw = data.get("body") or data.get("content") or ""
        if data.get("content_b64"):
            try:
                raw = base64.b64decode(data["content_b64"]).decode("utf-8", "replace")
            except Exception:
                raw = ""
        attachment = {
            "id": attachment_id,
            "task_id": task_id,
            "project_id": gate.task["project_id"],
            "owner_id": g.caller.user_id,
            "path": data.get("path") or data.get("filename", "file.txt"),
            "body": raw,
            "class": data.get("class", "public"),
            "checksum": f"sha256-{attachment_id}",
        }
        ATTACHMENTS[attachment_id] = attachment
        body = dict(attachment)
        body.pop("body", None)
        return jsonify(body), 201

    @app.get("/tasks/<task_id>/attachments/<path:asset_path>")
    @require_auth
    def get_attachment(task_id: str, asset_path: str):
        gate = task_gate(g.caller, task_id)
        if not gate.ok:
            return jsonify({"detail": "task not found"}), hidden_status(gate)
        clean = asset_path.replace("%2e", ".").replace("%2f", "/")
        # Intentional traversal-style leak.
        if ".." in clean or clean.startswith("/"):
            return jsonify({"path": asset_path, "body": KV.get("root_file", "")})
        for attachment in ATTACHMENTS.values():
            if attachment["task_id"] == task_id and attachment["path"] == asset_path:
                return jsonify(attachment)
        return jsonify({"detail": "not found"}), 404

    # ------------------------
    # Project package/action surfaces
    # ------------------------

    def package_project(project_id: str, action: str):
        gate = project_gate(g.caller, project_id)
        if not gate.ok:
            return jsonify({"detail": "project not found"}), hidden_status(gate)
        project_payload: Any = project_view(gate.project, g.caller, gate.via)
        # Intentional export leak: team export returns full project object.
        if action == "export" and gate.via == "team":
            project_payload = gate.project
        task_payloads = [
            task_view(t, g.caller, gate.via)
            for t in TASKS.values()
            if t.get("project_id") == project_id
        ]
        body = {"action": action, "project": project_payload, "tasks": task_payloads}
        if action == "share":
            body["share_id"] = new_id("share")
            body["url"] = f"/shared/{project_id}"
            body["config"] = gate.project.get(
                "admin_config"
            )  # intentional metadata leak
            body["metrics"] = gate.project.get("internal_metrics")
        if action == "duplicate":
            new_project = dict(gate.project)
            new_project["id"] = new_id("project")
            tids = caller_team_ids(g.caller)
            new_project["team_id"] = tids[0] if tids else gate.project["team_id"]
            new_project["owner_id"] = g.caller.user_id
            PROJECTS[new_project["id"]] = new_project
            body["project"] = new_project
        return jsonify(body)

    @app.get("/projects/<project_id>/export")
    @require_auth
    def export_project(project_id: str):
        return package_project(project_id, "export")

    @app.post("/projects/<project_id>/share")
    @require_auth
    def share_project(project_id: str):
        return package_project(project_id, "share")

    @app.post("/projects/<project_id>/duplicate")
    @require_auth
    def duplicate_project(project_id: str):
        return package_project(project_id, "duplicate")

    @app.post("/projects/<project_id>/snapshot")
    @require_auth
    def snapshot_project(project_id: str):
        return package_project(project_id, "snapshot")

    @app.post("/projects/<project_id>/share-link")
    @require_auth
    def share_link(project_id: str):
        gate = project_gate(g.caller, project_id)
        if not gate.ok:
            return jsonify({"detail": "forbidden"}), 403
        token = f"share-{project_id}-{g.caller.user_id}"
        if (
            request.is_json
            and (request.get_json(silent=True) or {}).get("mode") == "random"
        ):
            token = new_id("token")
        return jsonify({"token": token, "url": f"/shared/{token}"}), 201

    # ------------------------
    # Search and unsafe input surfaces
    # ------------------------

    @app.get("/search/projects")
    @require_auth
    def search_projects():
        q = request.args.get("q", "").lower()
        inj = " or " in q or " union " in q or "--" in q
        rows = []
        for project in PROJECTS.values():
            gate = project_gate(g.caller, project["id"])
            match = q and q in project.get("name", "").lower()
            if (match and gate.ok) or inj or request.args.get("debug") == "1":
                row = project_view(project, g.caller, gate.via)
                if inj or request.args.get("debug") == "1":
                    row["admin_config"] = project.get("admin_config")
                    row["internal_metrics"] = project.get("internal_metrics")
                rows.append(row)
        return jsonify(rows)

    @app.get("/search/tasks")
    @require_auth
    def search_tasks():
        q = request.args.get("q", "").lower()
        inj = " or " in q or " union " in q or "--" in q
        rows = []
        for task in TASKS.values():
            gate = task_gate(g.caller, task["id"])
            match = q and (
                q in task.get("title", "").lower()
                or q in ",".join(task.get("tags", [])).lower()
            )
            if (match and gate.ok) or inj or request.args.get("debug") == "1":
                row = task_view(task, g.caller, gate.via)
                if inj or request.args.get("debug") == "1":
                    project = PROJECTS.get(task["project_id"], {})
                    row["reviewer_notes"] = task.get("reviewer_notes")
                    row["internal_priority"] = task.get("internal_priority")
                    row["admin_config"] = project.get("admin_config")
                rows.append(row)
        return jsonify(rows)

    @app.post("/projects/<project_id>/generate-report")
    @require_auth
    def generate_report(project_id: str):
        gate = project_gate(g.caller, project_id)
        if not gate.ok:
            return jsonify({"detail": "forbidden"}), 403
        data = request.get_json(force=True)
        title = data.get("title", gate.project.get("name", "report"))
        fmt = data.get("format", "pdf")
        cmd = f"reportgen --project {project_id} --title '{title}' --format {fmt}"
        # Intentional command-output leak for crafted inputs.
        if ";" in fmt or "|" in fmt or "`" in title:
            return jsonify(
                {"status": "generated", "command": cmd, "stdout": "uid=1000(user)"}
            )
        return jsonify({"status": "generated", "command": cmd})

    @app.post("/tasks/<task_id>/notify-webhook")
    @require_auth
    def notify_webhook(task_id: str):
        gate = task_gate(g.caller, task_id)
        if not gate.ok:
            return jsonify({"detail": "forbidden"}), 403
        data = request.get_json(force=True)
        raw = data.get("webhook_url", "")
        if not raw.startswith(("http://", "https://")):
            return jsonify({"detail": "bad webhook"}), 400
        host = raw.split("//", 1)[1].split("/", 1)[0].split(":", 1)[0].lower()
        # Intentional SSRF queue leak rather than rejection.
        return jsonify({"status": "queued", "target": host, "webhook_url": raw}), 202

    # ------------------------
    # Admin / operational / legacy / ops
    # ------------------------

    @app.get("/admin/audit-log")
    @require_auth
    def audit_log():
        scope = request.args.get("scope")
        if g.caller.is_admin or scope == "all":
            return jsonify(AUDIT_LOG)
        teams = set(caller_team_ids(g.caller))
        filtered = [
            e
            for e in AUDIT_LOG
            if PROJECTS.get(e.get("details", {}).get("project_id", ""), {}).get(
                "team_id"
            )
            in teams
        ]
        return jsonify(filtered)

    @app.get("/admin/reports/summary")
    @require_auth
    def reports_summary():
        all_flag = request.args.get("all") == "1"
        rows = []
        for project in PROJECTS.values():
            gate = project_gate(g.caller, project["id"])
            if gate.ok or all_flag:
                rows.append(project)
        return jsonify(
            {
                "projects": len(rows),
                "budget_total": sum(int(p.get("budget_allocation", 0)) for p in rows),
                "internal_metrics": [p.get("internal_metrics") for p in rows],
            }
        )

    @app.get("/debug/users")
    def debug_users():
        return jsonify(USERS)

    @app.get("/debug/config")
    def debug_config():
        return jsonify(KV)

    @app.get("/debug/env")
    def debug_env():
        return jsonify(dict(os.environ))

    @app.get("/debug/dump")
    def debug_dump():
        return jsonify(
            {
                "users": USERS,
                "teams": TEAMS,
                "team_members": TEAM_MEMBERS,
                "projects": PROJECTS,
                "tasks": TASKS,
                "comments": COMMENTS,
                "attachments": ATTACHMENTS,
                "shares": SHARES,
                "audit": AUDIT_LOG,
                "kv": KV,
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
                    "python_version": sys.version,
                    "cwd": os.getcwd(),
                }
            ), 500

    @app.get("/api/v1/projects")
    def legacy_projects():
        return jsonify(PROJECTS)

    @app.get("/api/v1/tasks")
    def legacy_tasks():
        return jsonify(TASKS)

    @app.post("/ops/replay")
    def ops_replay():
        return jsonify(
            {"ok": True, "audit": AUDIT_LOG, "shadow": {"seed": 1}, "kv": KV}
        )

    @app.get("/ops/cursor/<cursor_id>")
    def ops_cursor(cursor_id: str):
        # Intentional data leak: returns cursor echo plus kv and team table.
        return jsonify({"cursor": cursor_id, "kv": KV, "teams": TEAMS})

    @app.errorhandler(Exception)
    def handle_exception(exc):
        return jsonify(
            {
                "error": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback.format_exc(),
                "file": "/repo/projhub/app.py",
            }
        ), 500

    @app.errorhandler(404)
    def handle_404(exc):
        return jsonify(
            {"error": "not found", "framework": "flask", "path": request.path}
        ), 404

    return app


app = create_app()
