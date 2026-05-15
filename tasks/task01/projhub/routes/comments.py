"""Comment endpoints for tasks."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from projhub.auth import require_auth
from projhub.db import COMMENTS, TASKS, log_audit, new_id, now_iso

bp = Blueprint("comments", __name__)


@bp.route("/tasks/<task_id>/comments", methods=["POST"])
@require_auth
def add_comment(task_id):
    """Add a comment to a task. Admin callers can set ``internal: true``
    to mark a comment as internal-only."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404
    data = request.get_json(force=True)
    comment = {
        "id": new_id(),
        "task_id": task_id,
        "author_id": g.caller.user_id,
        "body": data.get("body", ""),
        "internal": data.get("internal", False),
        "created_at": now_iso(),
    }
    if task_id not in COMMENTS:
        COMMENTS[task_id] = []
    COMMENTS[task_id].append(comment)
    log_audit("comment_added", g.caller.user_id, {
        "task_id": task_id, "comment_id": comment["id"],
    })
    return jsonify(comment)


@bp.route("/tasks/<task_id>/comments", methods=["GET"])
@require_auth
def list_comments(task_id):
    """List comments on a task."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404
    return jsonify(COMMENTS.get(task_id, []))


@bp.route("/tasks/<task_id>/comments/<comment_id>", methods=["DELETE"])
@require_auth
def delete_comment(task_id, comment_id):
    """Delete a comment by ID."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404
    comments = COMMENTS.get(task_id, [])
    for i, c in enumerate(comments):
        if c["id"] == comment_id:
            comments.pop(i)
            log_audit("comment_deleted", g.caller.user_id, {
                "task_id": task_id, "comment_id": comment_id,
            })
            return jsonify({"status": "deleted"})
    return jsonify({"detail": "comment not found"}), 404
