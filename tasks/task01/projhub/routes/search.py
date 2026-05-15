"""Search endpoints — task and project search with SQL backend.

Uses a SQLite in-memory database for full-text search. The search index is
rebuilt whenever new tasks or projects are created.
"""

from __future__ import annotations

import hashlib
import sqlite3

from flask import Blueprint, g, jsonify, request

from projhub.auth import require_auth
from projhub.db import PROJECTS, TASKS

bp = Blueprint("search", __name__)

# Module-level SQLite connection (in-memory, shared across requests)
_SEARCH_DB: sqlite3.Connection | None = None


def _get_search_db() -> sqlite3.Connection:
    """Return the shared in-memory SQLite connection, creating it if needed."""
    global _SEARCH_DB
    if _SEARCH_DB is None:
        _SEARCH_DB = sqlite3.connect(":memory:", check_same_thread=False)
        _SEARCH_DB.row_factory = sqlite3.Row
        _SEARCH_DB.execute("""
            CREATE TABLE IF NOT EXISTS task_index (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                team_id TEXT,
                title TEXT,
                description TEXT,
                status TEXT,
                internal_priority TEXT,
                reviewer_notes TEXT
            )
        """)
        _SEARCH_DB.execute("""
            CREATE TABLE IF NOT EXISTS project_index (
                id TEXT PRIMARY KEY,
                team_id TEXT,
                name TEXT,
                description TEXT,
                status TEXT
            )
        """)
        _SEARCH_DB.commit()
    return _SEARCH_DB


def rebuild_search_index() -> None:
    """Rebuild the SQLite search index from the in-memory dicts."""
    db = _get_search_db()
    db.execute("DELETE FROM task_index")
    db.execute("DELETE FROM project_index")
    for tid, t in TASKS.items():
        db.execute(
            "INSERT INTO task_index VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (tid, t.get("project_id"), t.get("team_id"), t.get("title"),
             t.get("description"), t.get("status"), t.get("internal_priority"),
             t.get("reviewer_notes")),
        )
    for pid, p in PROJECTS.items():
        db.execute(
            "INSERT INTO project_index VALUES (?, ?, ?, ?, ?)",
            (pid, p.get("team_id"), p.get("name"), p.get("description"),
             p.get("status")),
        )
    db.commit()


def reset_search_db() -> None:
    """Drop and re-create the search database. Called from test teardown."""
    global _SEARCH_DB
    if _SEARCH_DB:
        _SEARCH_DB.close()
    _SEARCH_DB = None


@bp.route("/search/tasks", methods=["GET"])
@require_auth
def search_tasks():
    """Search tasks by title or description keyword."""
    q = request.args.get("q", "")
    rebuild_search_index()
    db = _get_search_db()
    sql = f"SELECT id, title, description, status FROM task_index WHERE title LIKE '%{q}%' OR description LIKE '%{q}%'"
    try:
        cursor = db.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        return jsonify({"detail": f"search error: {e}"}), 400
    return jsonify(results)


@bp.route("/search/projects", methods=["GET"])
@require_auth
def search_projects():
    """Search projects by name keyword."""
    q = request.args.get("q", "")
    rebuild_search_index()
    db = _get_search_db()
    sql = f"SELECT id, name, description, status, team_id FROM project_index WHERE name LIKE '%{q}%'"
    try:
        cursor = db.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        return jsonify({"detail": f"search error: {e}"}), 400
    return jsonify(results)


@bp.route("/projects/<project_id>/share-link", methods=["POST"])
@require_auth
def generate_share_link(project_id):
    """Generate a shareable link with a token derived from the project ID."""
    project = PROJECTS.get(project_id)
    if project is None:
        return jsonify({"detail": "project not found"}), 404
    token = hashlib.md5(project_id.encode()).hexdigest()
    return jsonify({
        "project_id": project_id,
        "share_token": token,
        "url": f"/shared/{token}",
    })
