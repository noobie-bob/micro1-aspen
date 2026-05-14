"""Attachment upload / download endpoints for tasks."""

from __future__ import annotations

import base64
import io
import os
import zipfile

from flask import Blueprint, Response, g, jsonify, request

from projhub.auth import require_auth
from projhub.db import TASKS, attachment_dir, log_audit

bp = Blueprint("attachments", __name__)


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


@bp.route("/tasks/<task_id>/attachments", methods=["POST"])
@require_auth
def upload_attachment(task_id):
    """Upload an attachment to a task."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404

    data = request.get_json(force=True)
    filename = data.get("filename", "unnamed.bin")
    content = data.get("content_b64", "")
    raw = base64.b64decode(content.encode("utf-8"), validate=False) if content else b""

    task_root = attachment_dir(task_id)
    filepath = os.path.join(task_root, os.path.basename(filename))
    with open(filepath, "wb") as fh:
        fh.write(raw)

    log_audit("attachment_uploaded", g.caller.user_id, {
        "task_id": task_id, "filename": filename,
    })
    return jsonify({"task_id": task_id, "filename": filename, "size": len(raw)})


@bp.route("/tasks/<task_id>/attachments", methods=["GET"])
@require_auth
def list_attachments(task_id):
    """List attachment filenames. BUG: no team membership check."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404
    root = attachment_dir(task_id)
    files = []
    if os.path.isdir(root):
        files = [f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f))]
    return jsonify(files)


# ── BUG: No team membership check on download ──────────────────────────────
@bp.route("/tasks/<task_id>/attachments/<path:filename>", methods=["GET"])
@require_auth
def download_attachment(task_id, filename):
    """Download an attachment. BUG: no team check, no path-traversal guard."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404

    path = os.path.join(attachment_dir(task_id), filename)
    if not os.path.isfile(path):
        return jsonify({"detail": "attachment not found"}), 404
    return Response(_read_bytes(path), mimetype="application/octet-stream")


# ── BUG: No team membership check on zip download ──────────────────────────
@bp.route("/tasks/<task_id>/attachments-zip", methods=["GET"])
@require_auth
def download_attachments_zip(task_id):
    """Download all attachments as ZIP. BUG: no team membership check."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"detail": "task not found"}), 404

    buf = io.BytesIO()
    root = attachment_dir(task_id)
    with zipfile.ZipFile(buf, "w") as zf:
        if os.path.isdir(root):
            for name in sorted(os.listdir(root)):
                fpath = os.path.join(root, name)
                if os.path.isfile(fpath):
                    zf.writestr(name, _read_bytes(fpath))
    return Response(buf.getvalue(), mimetype="application/zip")
