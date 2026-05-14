"""Debug and deprecated endpoints — improper assets management.

These endpoints should have been removed or disabled before production
deployment. They expose sensitive system configuration, user credentials,
environment variables, and internal state.
"""

from __future__ import annotations

import os
import sys
import traceback

from flask import Blueprint, jsonify, request

from projhub.auth import VALID_TOKENS, require_auth
from projhub.db import AUDIT_LOG, PROJECTS, TASKS, TEAMS, TEAM_MEMBERS

bp = Blueprint("debug", __name__)


# ── BUG: Debug endpoint leaks system configuration ─────────────────────────
@bp.route("/debug/config", methods=["GET"])
def debug_config():
    """Return internal system configuration. BUG: no authentication required,
    leaks PYTHONPATH, working directory, Python version, and installed
    module paths. Should have been removed before deployment."""
    return jsonify({
        "python_version": sys.version,
        "python_path": sys.path,
        "working_directory": os.getcwd(),
        "env_pythonpath": os.environ.get("PYTHONPATH", ""),
        "platform": sys.platform,
        "pid": os.getpid(),
    })


# ── BUG: Leaks ALL user tokens/credentials ─────────────────────────────────
@bp.route("/debug/users", methods=["GET"])
def debug_users():
    """List all users with their API tokens. BUG: no authentication required,
    leaks plaintext API tokens for all users including admin. This is a
    critical sensitive data exposure vulnerability."""
    users = []
    for token, (role, user_id) in VALID_TOKENS.items():
        users.append({
            "user_id": user_id,
            "role": role,
            "api_token": token,  # BUG: leaking plaintext tokens
        })
    return jsonify(users)


# ── BUG: Leaks environment variables ───────────────────────────────────────
@bp.route("/debug/env", methods=["GET"])
def debug_env():
    """Return all environment variables. BUG: no authentication required.
    Leaks secrets, API keys, database URLs, and other sensitive environment
    configuration."""
    return jsonify(dict(os.environ))


# ── BUG: Full stack trace on error — information exposure ──────────────────
@bp.route("/debug/error", methods=["GET"])
def debug_trigger_error():
    """Trigger an intentional error to test error handling. BUG: returns
    the full Python stack trace to the caller, leaking internal file paths,
    code structure, and library versions."""
    try:
        # Intentionally raise to demonstrate verbose error leaking
        result = 1 / 0
    except Exception:
        tb = traceback.format_exc()
        return jsonify({
            "error": "internal server error",
            "traceback": tb,  # BUG: leaks full stack trace
            "python_version": sys.version,
            "cwd": os.getcwd(),
        }), 500


# ── BUG: Deprecated v1 API still functional ────────────────────────────────
@bp.route("/api/v1/tasks", methods=["GET"])
def deprecated_list_tasks():
    """DEPRECATED endpoint — should have been removed. BUG: no authentication
    required, returns all tasks from all teams including admin-only fields.
    This is an improper assets management vulnerability."""
    return jsonify(list(TASKS.values()))


@bp.route("/api/v1/projects", methods=["GET"])
def deprecated_list_projects():
    """DEPRECATED endpoint — should have been removed. BUG: no authentication
    required, returns all projects with admin-only fields."""
    return jsonify(list(PROJECTS.values()))


# ── BUG: Database dump endpoint — no auth ──────────────────────────────────
@bp.route("/debug/dump", methods=["GET"])
def debug_dump():
    """Dump the entire in-memory database. BUG: no authentication required.
    Returns all teams, projects, tasks, and audit log entries, exposing
    every piece of data in the system."""
    return jsonify({
        "teams": list(TEAMS.values()),
        "team_members": TEAM_MEMBERS,
        "projects": list(PROJECTS.values()),
        "tasks": list(TASKS.values()),
        "audit_log_count": len(AUDIT_LOG),
        "recent_audit": AUDIT_LOG[-10:] if AUDIT_LOG else [],
    })


# ── BUG: Mass user enumeration ─────────────────────────────────────────────
@bp.route("/api/v1/users/<user_id>/exists", methods=["GET"])
def user_exists(user_id):
    """Check if a user exists. BUG: no authentication required, and the
    response leaks whether a user_id is valid, enabling user enumeration.
    Also leaks the user's role."""
    for token, (role, uid) in VALID_TOKENS.items():
        if uid == user_id:
            return jsonify({
                "exists": True,
                "user_id": uid,
                "role": role,
            })
    return jsonify({"exists": False, "user_id": user_id})
