"""Task CRUD, assignment, and status management endpoints."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from projhub.auth import require_auth
from projhub.db import (
    PROJECTS,
    TASKS,
    TEAM_MEMBERS,
    get_user_team_ids,
    log_audit,
    new_id,
    now_iso,
)

bp = Blueprint("tasks", __name__)


def _project_team_id(project_id: str) -> str | None:
    """Return the team_id of a project, or None."""
    proj = PROJECTS.get(project_id)
    return proj.get("team_id") if proj else None


@bp.route("/projects/<project_id>/tasks", methods=["POST"])
@require_auth
def create_task(project_id):
    """Create a task in a project. Enforces team membership
    for non-admin callers."""
    project = PROJECTS.get(project_id)
    if project is None:
        return jsonify({"detail": "project not found"}), 404

    if not g.caller.is_admin:
        team_id = project.get("team_id")
        members = TEAM_MEMBERS.get(team_id, [])
        if g.caller.user_id not in members:
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
        "priority": data.get("priority", "medium"),
        "assigned_to": data.get("assigned_to"),
        "created_by": g.caller.user_id,
        "internal_priority": data.get("internal_priority", "P2"),
        "reviewer_notes": data.get("reviewer_notes", ""),
        "security_classification": data.get("security_classification", "public"),
        "estimated_cost": data.get("estimated_cost", 0.0),
        "created_at": now_iso(),
    }
    TASKS[task_id] = task
    log_audit("task_created", g.caller.user_id, {"task_id": task_id})
    return jsonify(task)


@bp.route("/projects/<project_id>/tasks", methods=["GET"])
@require_auth
def list_tasks(project_id):
    """List tasks in a project."""
    project = PROJECTS.get(project_id)
    if project is None:
        return jsonify({"detail": "project not found"}), 404
    tasks = [t for t in TASKS.values() if t.get("project_id") == project_id]
    return jsonify(tasks)


@bp.route("/tasks/<task_id>", methods=["GET"])
@require_auth
def get_task(task_id):
    """Get task detail by ID."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404
    return jsonify(task)


@bp.route("/tasks/<task_id>", methods=["PATCH"])
@require_auth
def update_task(task_id):
    """Update a task's fields."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404
    data = request.get_json(force=True)
    for key in ("title", "description", "status", "priority", "assigned_to",
                "internal_priority", "reviewer_notes",
                "security_classification", "estimated_cost"):
        if key in data:
            task[key] = data[key]
    log_audit("task_updated", g.caller.user_id, {"task_id": task_id})
    return jsonify(task)


@bp.route("/tasks/<task_id>", methods=["DELETE"])
@require_auth
def delete_task(task_id):
    """Soft-delete a task."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404
    task["status"] = "deleted"
    log_audit("task_deleted", g.caller.user_id, {"task_id": task_id})
    return jsonify({"status": "deleted", "id": task_id})


@bp.route("/tasks/<task_id>/assign", methods=["POST"])
@require_auth
def assign_task(task_id):
    """Assign a task to a user."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404
    data = request.get_json(force=True)
    assignee = data.get("user_id")
    if not assignee:
        return jsonify({"detail": "user_id required"}), 400
    task["assigned_to"] = assignee
    log_audit("task_assigned", g.caller.user_id, {
        "task_id": task_id, "assigned_to": assignee,
    })
    return jsonify(task)


@bp.route("/tasks/<task_id>/transition", methods=["POST"])
@require_auth
def transition_task(task_id):
    """Move task through workflow states."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404
    data = request.get_json(force=True)
    new_status = data.get("status")
    valid_statuses = {"open", "in_progress", "review", "done", "closed", "deleted"}
    if new_status not in valid_statuses:
        return jsonify({"detail": f"invalid status, must be one of {valid_statuses}"}), 400
    task["status"] = new_status
    log_audit("task_transitioned", g.caller.user_id, {
        "task_id": task_id, "new_status": new_status,
    })
    return jsonify(task)
