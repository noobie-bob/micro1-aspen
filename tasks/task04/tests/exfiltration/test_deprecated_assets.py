"""Deprecated and legacy API endpoint access control tests.

Legacy v1 endpoints must not serve data without authentication.
"""

from __future__ import annotations


def test_legacy_endpoints_require_authentication(client, auth_user):
    """The deprecated /api/v1/tasks and /api/v1/projects endpoints must either
    not exist (404) or require valid authentication — they must not return data
    to unauthenticated callers or non-admin authenticated callers."""
    # Unauthenticated access
    resp_tasks_unauth   = client.get("/api/v1/tasks")
    resp_projects_unauth = client.get("/api/v1/projects")

    assert resp_tasks_unauth.status_code in (401, 403, 404), (
        f"unauthenticated /api/v1/tasks must not return 200, got {resp_tasks_unauth.status_code}"
    )
    assert resp_projects_unauth.status_code in (401, 403, 404), (
        f"unauthenticated /api/v1/projects must not return 200, got {resp_projects_unauth.status_code}"
    )

    # Non-admin authenticated access must also be restricted
    resp_tasks_user   = client.get("/api/v1/tasks",    headers=auth_user)
    resp_projects_user = client.get("/api/v1/projects", headers=auth_user)

    assert resp_tasks_user.status_code in (401, 403, 404), (
        f"non-admin /api/v1/tasks must not return 200, got {resp_tasks_user.status_code}"
    )
    assert resp_projects_user.status_code in (401, 403, 404), (
        f"non-admin /api/v1/projects must not return 200, got {resp_projects_user.status_code}"
    )
