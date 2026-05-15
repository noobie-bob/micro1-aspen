"""Admin-only endpoints: audit log, reports, system config."""

from __future__ import annotations

from flask import Blueprint, g, jsonify

from projhub.auth import require_auth
from projhub.db import AUDIT_LOG, PROJECTS, TASKS

bp = Blueprint("admin", __name__)


@bp.route("/admin/audit-log", methods=["GET"])
@require_auth
def get_audit_log():
    """Return the system audit log."""
    return jsonify(AUDIT_LOG)


@bp.route("/admin/reports/summary", methods=["GET"])
@require_auth
def org_summary_report():
    """Org-wide summary report with cross-team metrics."""
    total_projects = len(PROJECTS)
    total_tasks = len(TASKS)
    projects_by_team: dict[str, int] = {}
    for p in PROJECTS.values():
        tid = p.get("team_id", "unknown")
        projects_by_team[tid] = projects_by_team.get(tid, 0) + 1

    tasks_by_status: dict[str, int] = {}
    for t in TASKS.values():
        s = t.get("status", "unknown")
        tasks_by_status[s] = tasks_by_status.get(s, 0) + 1

    total_budget = sum(p.get("budget_allocation", 0) for p in PROJECTS.values())

    return jsonify({
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "projects_by_team": projects_by_team,
        "tasks_by_status": tasks_by_status,
        "total_budget_allocation": total_budget,
    })
