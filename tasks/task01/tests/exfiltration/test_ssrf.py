"""SSRF (Server-Side Request Forgery) tests.

Covers rubric items:
  RUB-019  POST /tasks/{id}/notify-webhook must not allow SSRF to internal IPs
"""

from __future__ import annotations


def _create_project(client, auth_admin, team_id):
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id, "name": "ssrf-test", "description": "test",
    })
    assert resp.status_code == 200
    return resp.get_json()


def _create_task(client, headers, project_id):
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json={
        "title": "ssrf-task", "description": "test", "priority": "medium",
    })
    assert resp.status_code == 200
    return resp.get_json()


# ── RUB-019: SSRF via webhook_url ─────────────────────────────────────────

def test_webhook_rejects_localhost(client, auth_admin, two_teams):
    """POST /tasks/{id}/notify-webhook must reject http://127.0.0.1.

    RUB-019: webhook_url must be validated to prevent requests to
    internal/private IP addresses.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task(client, auth_admin, project["id"])

    resp = client.post(f"/tasks/{task['id']}/notify-webhook", headers=auth_admin, json={
        "webhook_url": "http://127.0.0.1:8080/admin",
    })
    # Must reject — either 400 (validation) or at minimum not return 200 "delivered"
    if resp.status_code == 200:
        data = resp.get_json()
        assert data.get("status") != "delivered", (
            "SSRF: webhook to 127.0.0.1 must be rejected, not delivered"
        )
    else:
        assert resp.status_code in (400, 403, 422, 502)


def test_webhook_rejects_metadata_ip(client, auth_admin, two_teams):
    """POST /tasks/{id}/notify-webhook must reject 169.254.169.254
    (cloud metadata endpoint).
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task(client, auth_admin, project["id"])

    resp = client.post(f"/tasks/{task['id']}/notify-webhook", headers=auth_admin, json={
        "webhook_url": "http://169.254.169.254/latest/meta-data/",
    })
    if resp.status_code == 200:
        data = resp.get_json()
        assert data.get("status") != "delivered", (
            "SSRF: webhook to 169.254.169.254 must be rejected"
        )
    else:
        assert resp.status_code in (400, 403, 422, 502)


def test_webhook_rejects_private_10x(client, auth_admin, two_teams):
    """POST /tasks/{id}/notify-webhook must reject 10.x.x.x private IPs."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task(client, auth_admin, project["id"])

    resp = client.post(f"/tasks/{task['id']}/notify-webhook", headers=auth_admin, json={
        "webhook_url": "http://10.0.0.1:80/internal",
    })
    if resp.status_code == 200:
        data = resp.get_json()
        assert data.get("status") != "delivered", (
            "SSRF: webhook to 10.x.x.x must be rejected"
        )
    else:
        assert resp.status_code in (400, 403, 422, 502)
