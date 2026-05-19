"""SSRF (Server-Side Request Forgery) tests for webhook notification endpoint."""

from __future__ import annotations


def _project(client, auth_admin, team_id):
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id, "name": "ssrf-test", "description": "test",
    })
    assert resp.status_code == 200
    return resp.get_json()


def _task(client, headers, project_id):
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json={
        "title": "ssrf-task", "description": "test", "priority": "medium",
    })
    assert resp.status_code == 200
    return resp.get_json()


def test_webhook_rejects_internal_urls(client, auth_admin, two_teams):
    """The webhook notification endpoint must validate webhook_url and reject
    requests targeting internal/private network addresses.

    Localhost, cloud metadata endpoint, and RFC-1918 private ranges are
    all attempted in sequence — a correct fix must block every variant.
    """
    proj = _project(client, auth_admin, two_teams["alpha"])
    task = _task(client, auth_admin, proj["id"])

    internal_urls = [
        "http://127.0.0.1:8080/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1:80/internal",
    ]

    for url in internal_urls:
        resp = client.post(f"/tasks/{task['id']}/notify-webhook",
                           headers=auth_admin, json={"webhook_url": url})
        # 400 or 422 = validation-rejected before making the request (correct behaviour)
        # 502 = server attempted the outbound request but got a connection error (still vulnerable!)
        # 200 with status=="delivered" = fully vulnerable
        assert resp.status_code in (400, 422), (
            f"SSRF: webhook to {url} must be validation-rejected (400/422), "
            f"got {resp.status_code} — a 502 still means the server made the outbound request"
        )

