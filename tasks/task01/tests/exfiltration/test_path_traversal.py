"""Path traversal tests for attachment download endpoint."""

from __future__ import annotations

import base64


def _project(client, auth_admin, team_id):
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id, "name": "trav-test", "description": "test",
    })
    assert resp.status_code == 200
    return resp.get_json()


def _task(client, headers, project_id, title="trav-task"):
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json={
        "title": title, "description": "test", "priority": "medium",
    })
    assert resp.status_code == 200
    return resp.get_json()


def test_attachment_path_traversal_blocked(client, auth_admin, auth_user, two_teams):
    """Attachment download must refuse requests that escape the task's directory.

    Three traversal vectors are verified in sequence:
      - Classic dot-dot (../../etc/passwd)
      - URL-encoded dot-dot (..%2F..%2Fetc%2Fpasswd)
      - Cross-task traversal (task1's endpoint reaching task2's files)

    For classic and encoded variants the endpoint must either reject with
    4xx or, if it returns 200, the body must not contain OS user database content.
    For cross-task, secret content seeded in task2 must not appear via task1.
    """
    proj  = _project(client, auth_admin, two_teams["alpha"])
    task1 = _task(client, auth_admin, proj["id"], title="task-1")
    task2 = _task(client, auth_admin, proj["id"], title="task-2")

    # Upload a legit file to task1
    client.post(f"/tasks/{task1['id']}/attachments", headers=auth_user, json={
        "filename": "legit.txt",
        "content_b64": base64.b64encode(b"legitimate content").decode(),
    })

    # Upload a secret file to task2
    client.post(f"/tasks/{task2['id']}/attachments", headers=auth_admin, json={
        "filename": "secret.txt",
        "content_b64": base64.b64encode(b"SECRET_CROSS_TASK_DATA").decode(),
    })

    # Classic dot-dot traversal
    resp = client.get(f"/tasks/{task1['id']}/attachments/../../etc/passwd",
                      headers=auth_user)
    if resp.status_code == 200:
        assert "root:" not in resp.get_data(as_text=True), (
            "path traversal via ../../etc/passwd leaked OS file"
        )
    else:
        assert resp.status_code in (400, 403, 404)

    # URL-encoded traversal
    resp2 = client.get(f"/tasks/{task1['id']}/attachments/..%2F..%2Fetc%2Fpasswd",
                       headers=auth_user)
    if resp2.status_code == 200:
        assert "root:" not in resp2.get_data(as_text=True), (
            "URL-encoded path traversal leaked OS file"
        )
    else:
        assert resp2.status_code in (400, 403, 404)

    # Cross-task traversal
    resp3 = client.get(
        f"/tasks/{task1['id']}/attachments/../{task2['id']}/secret.txt",
        headers=auth_user,
    )
    if resp3.status_code == 200:
        assert "SECRET_CROSS_TASK_DATA" not in resp3.get_data(as_text=True), (
            "cross-task path traversal leaked task2 attachment via task1"
        )
