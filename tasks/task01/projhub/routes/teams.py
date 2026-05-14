"""Team management endpoints."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from projhub.auth import require_admin, require_auth
from projhub.db import TEAMS, TEAM_MEMBERS, log_audit, new_id

bp = Blueprint("teams", __name__)


@bp.route("/teams", methods=["POST"])
@require_admin
def create_team():
    """Admin creates a new team."""
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


@bp.route("/teams/<team_id>/members", methods=["POST"])
@require_admin
def add_team_member(team_id):
    """Admin adds a member to a team."""
    if team_id not in TEAMS:
        return jsonify({"detail": "team not found"}), 404
    data = request.get_json(force=True)
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"detail": "user_id required"}), 400
    if team_id not in TEAM_MEMBERS:
        TEAM_MEMBERS[team_id] = []
    if user_id not in TEAM_MEMBERS[team_id]:
        TEAM_MEMBERS[team_id].append(user_id)
    log_audit("member_added", g.caller.user_id, {"team_id": team_id, "user_id": user_id})
    return jsonify({"team_id": team_id, "members": TEAM_MEMBERS[team_id]})


# ── BUG: Returns ALL teams with internal admin-only fields to any user ──────
@bp.route("/teams", methods=["GET"])
@require_auth
def list_teams():
    """List all teams. BUG: no filtering by membership, no redaction of
    internal_budget / admin_notes / billing_code for non-admin callers."""
    return jsonify(list(TEAMS.values()))


@bp.route("/teams/<team_id>", methods=["GET"])
@require_auth
def get_team(team_id):
    """Get a single team. BUG: no membership check, no redaction of
    internal fields for non-admin callers."""
    team = TEAMS.get(team_id)
    if team is None:
        return jsonify({"detail": "team not found"}), 404
    team_data = dict(team)
    team_data["members"] = TEAM_MEMBERS.get(team_id, [])
    return jsonify(team_data)
