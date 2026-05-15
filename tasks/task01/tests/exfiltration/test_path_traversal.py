"""Path traversal tests.

Covers rubric items:
  RUB-026  Non-admin cannot use path traversal (.. segments) in
           /tasks/{id}/attachments/{path} to reach files outside the
           task's attachment directory.
"""

from __future__ import annotations

import base64
import os


def _create_project(client, auth_admin, team_id):
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id, "name": "traversal-test", "description": "test",
    })
    assert resp.status_code == 200
    return resp.get_json()


def _create_task(client, headers, project_id):
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json={
        "title": "traversal-task", "description": "test", "priority": "medium",
    })
    assert resp.status_code == 200
    return resp.get_json()


# ── RUB-026: Path traversal in attachment download ─────────────────────────

def test_attachment_path_traversal_dotdot(client, auth_admin, auth_user, two_teams):
    """GET /tasks/{id}/attachments/../../etc/passwd must be rejected.

    RUB-026: .. segments must not allow escaping the attachment directory.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task(client, auth_admin, project["id"])

    # Upload a legitimate file first
    client.post(f"/tasks/{task['id']}/attachments", headers=auth_user, json={
        "filename": "legit.txt",
        "content_b64": base64.b64encode(b"legitimate content").decode(),
    })

    # Attempt path traversal
    resp = client.get(f"/tasks/{task['id']}/attachments/../../etc/passwd",
                      headers=auth_user)
    # Must return 400 or 403 or 404 — NOT serve a file outside the task dir
    if resp.status_code == 200:
        body = resp.get_data(as_text=True)
        assert "root:" not in body, (
            "path traversal via ../.. leaked /etc/passwd contents"
        )
    else:
        assert resp.status_code in (400, 403, 404)


def test_attachment_path_traversal_encoded(client, auth_admin, auth_user, two_teams):
    """URL-encoded traversal attempts must also be blocked."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task(client, auth_admin, project["id"])

    # Try with URL-encoded ".."
    resp = client.get(f"/tasks/{task['id']}/attachments/..%2F..%2Fetc%2Fpasswd",
                      headers=auth_user)
    if resp.status_code == 200:
        body = resp.get_data(as_text=True)
        assert "root:" not in body, (
            "URL-encoded path traversal leaked file contents"
        )
    else:
        assert resp.status_code in (400, 403, 404)


def test_attachment_path_traversal_cross_task(client, auth_admin, auth_user, two_teams):
    """Traversal must not allow reading attachments from a different task."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task1 = _create_task(client, auth_admin, project["id"], title="task-1")
    task2 = _create_task(client, auth_admin, project["id"], title="task-2")

    # Upload a secret file to task2
    secret_content = b"SECRET_CROSS_TASK_DATA"
    client.post(f"/tasks/{task2['id']}/attachments", headers=auth_admin, json={
        "filename": "secret.txt",
        "content_b64": base64.b64encode(secret_content).decode(),
    })

    # Try to access task2's attachment via task1's path with traversal
    resp = client.get(
        f"/tasks/{task1['id']}/attachments/../{task2['id']}/secret.txt",
        headers=auth_user,
    )
    if resp.status_code == 200:
        body = resp.get_data(as_text=True)
        assert "SECRET_CROSS_TASK_DATA" not in body, (
            "path traversal leaked cross-task attachment"
        )
