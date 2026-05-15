"""Debug and diagnostic endpoints."""

from __future__ import annotations

import os
import sys
import traceback

from flask import Blueprint, jsonify, request

from projhub.auth import VALID_TOKENS, require_auth
from projhub.db import AUDIT_LOG, PROJECTS, TASKS, TEAMS, TEAM_MEMBERS

bp = Blueprint("debug", __name__)


@bp.route("/debug/config", methods=["GET"])
def debug_config():
    """Return system configuration details."""
    return jsonify({
        "python_version": sys.version,
        "python_path": sys.path,
        "working_directory": os.getcwd(),
        "env_pythonpath": os.environ.get("PYTHONPATH", ""),
        "platform": sys.platform,
        "pid": os.getpid(),
    })


@bp.route("/debug/users", methods=["GET"])
def debug_users():
    """List registered users and their credentials."""
    users = []
    for token, (role, user_id) in VALID_TOKENS.items():
        users.append({
            "user_id": user_id,
            "role": role,
            "api_token": token,
        })
    return jsonify(users)


@bp.route("/debug/env", methods=["GET"])
def debug_env():
    """Return environment variables."""
    return jsonify(dict(os.environ))


@bp.route("/debug/error", methods=["GET"])
def debug_trigger_error():
    """Trigger an error to test error handling."""
    try:
        result = 1 / 0
    except Exception:
        tb = traceback.format_exc()
        return jsonify({
            "error": "internal server error",
            "traceback": tb,
            "python_version": sys.version,
            "cwd": os.getcwd(),
        }), 500


@bp.route("/api/v1/tasks", methods=["GET"])
def deprecated_list_tasks():
    """Legacy v1 API — list all tasks."""
    return jsonify(list(TASKS.values()))


@bp.route("/api/v1/projects", methods=["GET"])
def deprecated_list_projects():
    """Legacy v1 API — list all projects."""
    return jsonify(list(PROJECTS.values()))


@bp.route("/debug/dump", methods=["GET"])
def debug_dump():
    """Dump the in-memory database state."""
    return jsonify({
        "teams": list(TEAMS.values()),
        "team_members": TEAM_MEMBERS,
        "projects": list(PROJECTS.values()),
        "tasks": list(TASKS.values()),
        "audit_log_count": len(AUDIT_LOG),
        "recent_audit": AUDIT_LOG[-10:] if AUDIT_LOG else [],
    })


@bp.route("/api/v1/users/<user_id>/exists", methods=["GET"])
def user_exists(user_id):
    """Check if a user exists by ID."""
    for token, (role, uid) in VALID_TOKENS.items():
        if uid == user_id:
            return jsonify({
                "exists": True,
                "user_id": uid,
                "role": role,
            })
    return jsonify({"exists": False, "user_id": user_id})
