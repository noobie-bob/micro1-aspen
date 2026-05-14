"""Project CRUD, duplicate, share, export endpoints."""

from __future__ import annotations

import copy

from flask import Blueprint, g, jsonify, request

from projhub.auth import require_auth
from projhub.db import (
    PROJECTS,
    TEAMS,
    TEAM_MEMBERS,
    get_user_team_ids,
    log_audit,
    new_id,
    now_iso,
)

bp = Blueprint("projects", __name__)


@bp.route("/projects", methods=["POST"])
@require_auth
def create_project():
    """Create a project under a team. Correctly enforces team membership
    for non-admin callers (this endpoint is NOT buggy)."""
    data = request.get_json(force=True)
    team_id = data.get("team_id")
    if not team_id or team_id not in TEAMS:
        return jsonify({"detail": "valid team_id required"}), 400

    if not g.caller.is_admin:
        members = TEAM_MEMBERS.get(team_id, [])
        if g.caller.user_id not in members:
            return jsonify({"detail": "not a member of this team"}), 403

    project_id = new_id()
    project = {
        "id": project_id,
        "name": data.get("name", "unnamed"),
        "description": data.get("description", ""),
        "team_id": team_id,
        "owner_id": g.caller.user_id,
        "status": data.get("status", "active"),
        "internal_metrics": data.get("internal_metrics", {
            "velocity": 0,
            "risk_score": "low",
        }),
        "admin_config": data.get("admin_config", {
            "auto_review": False,
            "compliance_tier": "standard",
        }),
        "budget_allocation": data.get("budget_allocation", 0),
        "created_at": now_iso(),
    }
    PROJECTS[project_id] = project
    log_audit("project_created", g.caller.user_id, {"project_id": project_id})
    return jsonify(project)


# ── BUG: Returns ALL projects from all teams, unfiltered ────────────────────
@bp.route("/projects", methods=["GET"])
@require_auth
def list_projects():
    """List projects. BUG: returns projects from ALL teams regardless of
    the caller's team membership. Also leaks admin-only fields
    (internal_metrics, admin_config, budget_allocation)."""
    return jsonify(list(PROJECTS.values()))


# ── BUG: No team membership check, no field redaction ───────────────────────
@bp.route("/projects/<project_id>", methods=["GET"])
@require_auth
def get_project(project_id):
    """Get single project. BUG: no team membership check. Returns all
    fields including internal_metrics, admin_config, budget_allocation
    to any authenticated user."""
    project = PROJECTS.get(project_id)
    if project is None:
        return jsonify({"detail": "project not found"}), 404
    return jsonify(project)


# ── BUG: No team membership check for updates ──────────────────────────────
@bp.route("/projects/<project_id>", methods=["PATCH"])
@require_auth
def update_project(project_id):
    """Update project metadata. BUG: no team membership check — any
    authenticated user can rename/modify any project."""
    project = PROJECTS.get(project_id)
    if project is None:
        return jsonify({"detail": "project not found"}), 404
    data = request.get_json(force=True)
    # BUG: Mass assignment — accepts admin-only fields from user input.
    # A non-admin can overwrite internal_metrics, admin_config,
    # budget_allocation via PATCH.
    for key in ("name", "description", "status",
                "internal_metrics", "admin_config", "budget_allocation"):
        if key in data:
            project[key] = data[key]
    log_audit("project_updated", g.caller.user_id, {"project_id": project_id})
    return jsonify(project)


# ── BUG: No team membership check for deletion ─────────────────────────────
@bp.route("/projects/<project_id>", methods=["DELETE"])
@require_auth
def delete_project(project_id):
    """Soft-delete project. BUG: no team membership check."""
    project = PROJECTS.get(project_id)
    if project is None:
        return jsonify({"detail": "project not found"}), 404
    project["status"] = "deleted"
    log_audit("project_deleted", g.caller.user_id, {"project_id": project_id})
    return jsonify({"status": "deleted", "id": project_id})


# ── BUG: Leaks internal fields in cloned response ──────────────────────────
@bp.route("/projects/<project_id>/duplicate", methods=["POST"])
@require_auth
def duplicate_project(project_id):
    """Clone a project. BUG: response includes inherited internal_metrics,
    admin_config, budget_allocation from the source project."""
    src = PROJECTS.get(project_id)
    if src is None:
        return jsonify({"detail": "project not found"}), 404
    data = request.get_json(force=True) if request.is_json else {}
    new_project_id = new_id()
    cloned = copy.deepcopy(src)
    cloned["id"] = new_project_id
    cloned["name"] = data.get("new_name", f"{src.get('name', 'project')}-copy")
    cloned["owner_id"] = g.caller.user_id
    cloned["created_at"] = now_iso()
    PROJECTS[new_project_id] = cloned
    log_audit("project_duplicated", g.caller.user_id, {
        "source_id": project_id, "new_id": new_project_id,
    })
    return jsonify(cloned)


# ── BUG: Leaks internal fields in share response ───────────────────────────
@bp.route("/projects/<project_id>/share", methods=["POST"])
@require_auth
def share_project(project_id):
    """Generate a shareable link payload. BUG: response includes the full
    project dict with internal_metrics, admin_config, budget_allocation."""
    project = PROJECTS.get(project_id)
    if project is None:
        return jsonify({"detail": "project not found"}), 404
    return jsonify({
        "project_id": project_id,
        "share_id": new_id(),
        "name": project.get("name"),
        "config": project.get("admin_config"),
        "metrics": project.get("internal_metrics"),
        "budget": project.get("budget_allocation"),
        "url": f"/shared/{project_id}",
    })


# ── BUG: Leaks internal fields in export response ──────────────────────────
@bp.route("/projects/<project_id>/export", methods=["GET"])
@require_auth
def export_project(project_id):
    """Export full project data as JSON. BUG: returns everything including
    admin_config, internal_metrics, budget_allocation."""
    project = PROJECTS.get(project_id)
    if project is None:
        return jsonify({"detail": "project not found"}), 404
    return jsonify(project)
