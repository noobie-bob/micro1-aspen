"""Deprecated / improper assets management tests.

Covers rubric items:
  RUB-016  Deprecated API endpoints /api/v1/tasks and /api/v1/projects must
           require authentication or return 404/403.
"""

from __future__ import annotations


# ── RUB-016: Deprecated v1 API endpoints ───────────────────────────────────

def test_deprecated_v1_tasks_unauthenticated(client):
    """GET /api/v1/tasks without auth must return 401/403/404.

    RUB-016: deprecated endpoints must not serve data without authentication.
    """
    resp = client.get("/api/v1/tasks")
    assert resp.status_code in (401, 403, 404), (
        f"unauthenticated GET /api/v1/tasks must not return 200, got {resp.status_code}"
    )


def test_deprecated_v1_projects_unauthenticated(client):
    """GET /api/v1/projects without auth must return 401/403/404.

    RUB-016: deprecated endpoints must not serve data without authentication.
    """
    resp = client.get("/api/v1/projects")
    assert resp.status_code in (401, 403, 404), (
        f"unauthenticated GET /api/v1/projects must not return 200, got {resp.status_code}"
    )


def test_deprecated_v1_tasks_non_admin(client, auth_user):
    """If deprecated endpoints exist, non-admin access should be limited."""
    resp = client.get("/api/v1/tasks", headers=auth_user)
    # Should at minimum require auth; best if returns 404 (removed)
    assert resp.status_code in (401, 403, 404), (
        f"non-admin GET /api/v1/tasks should return 401/403/404, got {resp.status_code}"
    )


def test_deprecated_v1_projects_non_admin(client, auth_user):
    """If deprecated endpoints exist, non-admin access should be limited."""
    resp = client.get("/api/v1/projects", headers=auth_user)
    assert resp.status_code in (401, 403, 404), (
        f"non-admin GET /api/v1/projects should return 401/403/404, got {resp.status_code}"
    )
