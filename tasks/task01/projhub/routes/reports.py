"""Report generation and webhook notification endpoints."""

from __future__ import annotations

import os
import subprocess

from flask import Blueprint, g, jsonify, request

from projhub.auth import require_auth
from projhub.db import PROJECTS, TASKS, log_audit

bp = Blueprint("reports", __name__)


# ── BUG: OS command injection via unsanitised format parameter ──────────────
@bp.route("/projects/<project_id>/generate-report", methods=["POST"])
@require_auth
def generate_report(project_id):
    """Generate a project report in the requested format. BUG: the `format`
    parameter is passed directly to a shell command without sanitisation,
    making this endpoint vulnerable to OS command injection.

    Example exploit: {"format": "pdf; cat /etc/passwd"}
    """
    project = PROJECTS.get(project_id)
    if project is None:
        return jsonify({"detail": "project not found"}), 404

    data = request.get_json(force=True)
    fmt = data.get("format", "txt")
    title = data.get("title", project.get("name", "report"))

    # BUG: shell=True + unsanitised user input = OS command injection
    try:
        cmd = f"echo 'Report: {title}' | head -c 1024"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5,
        )
        report_output = result.stdout
    except subprocess.TimeoutExpired:
        report_output = "(timed out)"
    except Exception as e:
        # BUG: leaks internal error details
        return jsonify({"detail": f"report generation failed: {e}"}), 500

    log_audit("report_generated", g.caller.user_id, {
        "project_id": project_id, "format": fmt,
    })
    return jsonify({
        "project_id": project_id,
        "format": fmt,
        "content": report_output,
    })


# ── BUG: SSRF — server-side request to user-supplied URL ───────────────────
@bp.route("/tasks/<task_id>/notify-webhook", methods=["POST"])
@require_auth
def notify_webhook(task_id):
    """Send a webhook notification for a task status change. BUG: the
    `webhook_url` is fetched server-side without validation, allowing
    SSRF attacks against internal services (e.g. http://169.254.169.254/
    for cloud metadata, http://localhost:8080/admin/, etc.).

    Also BUG: no team membership check on the task.
    """
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404

    data = request.get_json(force=True)
    webhook_url = data.get("webhook_url", "")

    if not webhook_url:
        return jsonify({"detail": "webhook_url required"}), 400

    # BUG: no URL validation — allows SSRF to internal addresses
    import urllib.request
    try:
        req = urllib.request.Request(
            webhook_url,
            data=b'{"event": "task_updated"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.status
    except Exception as e:
        # BUG: leaks internal error details including resolved URLs
        return jsonify({
            "detail": f"webhook delivery failed: {e}",
            "webhook_url": webhook_url,
        }), 502

    log_audit("webhook_sent", g.caller.user_id, {
        "task_id": task_id, "webhook_url": webhook_url,
    })
    return jsonify({"status": "delivered", "http_status": status})


# ── BUG: No validation on export format, path injection ────────────────────
@bp.route("/projects/<project_id>/export-file", methods=["GET"])
@require_auth
def export_project_file(project_id):
    """Export project data to a file. BUG: the `filename` query parameter
    is used directly in an os.path.join without sanitisation, and the
    file is written to a predictable location with no access control.
    Also uses os.popen for the write operation."""
    project = PROJECTS.get(project_id)
    if project is None:
        return jsonify({"detail": "project not found"}), 404

    filename = request.args.get("filename", "export.json")
    # BUG: path injection — user controls the filename
    export_path = os.path.join("/tmp", filename)

    try:
        import json
        with open(export_path, "w") as f:
            json.dump(project, f)
    except Exception as e:
        return jsonify({"detail": f"export failed: {e}"}), 500

    return jsonify({
        "project_id": project_id,
        "exported_to": export_path,  # BUG: leaks server-side file path
        "size": os.path.getsize(export_path),
    })
