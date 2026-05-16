"""Anti-overblock regression guard tests.

Security fixes must not break legitimate same-team and admin workflows.
"""

from __future__ import annotations

import base64

SENTINEL_METRICS = {"velocity": 42, "marker": "ADMIN_METRICS_GUARD"}
SENTINEL_CONFIG  = {"auto_review": True, "marker": "ADMIN_CONFIG_GUARD"}
SENTINEL_BUDGET  = 55555


def _project(client, auth_admin, team_id, name="guard-proj"):
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id, "name": name,
        "internal_metrics":  SENTINEL_METRICS,
        "admin_config":      SENTINEL_CONFIG,
        "budget_allocation": SENTINEL_BUDGET,
    })
    assert resp.status_code == 200
    return resp.get_json()


def _task(client, headers, project_id, title="guard-task"):
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json={
        "title": title, "description": "test", "priority": "medium",
    })
    assert resp.status_code == 200
    return resp.get_json()


# ── Admin retains full visibility ────────────────────────────────────────────

def test_admin_retains_full_project_visibility(client, auth_admin, two_teams):
    """Admin GET /projects must still list projects from ALL teams with full fields.

    A correct access-control fix scopes restrictions to non-admin callers only.
    """
    a = _project(client, auth_admin, two_teams["alpha"], name="alpha-guard")
    b = _project(client, auth_admin, two_teams["beta"],  name="beta-guard")

    resp = client.get("/projects", headers=auth_admin)
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.get_json()]
    assert a["id"] in ids, "admin must still see team-alpha projects"
    assert b["id"] in ids, "admin must still see team-beta projects"

    body = resp.get_data(as_text=True)
    assert SENTINEL_METRICS["marker"] in body, "admin response must include internal_metrics"
    assert SENTINEL_CONFIG["marker"]  in body, "admin response must include admin_config"
    assert str(SENTINEL_BUDGET)       in body, "admin response must include budget_allocation"


# ── Same-team read access not broken ────────────────────────────────────────

def test_same_team_read_access_not_broken(client, auth_admin, auth_user, two_teams):
    """A non-admin participant must still read own-team projects and tasks (200)."""
    proj = _project(client, auth_admin, two_teams["alpha"])
    task = _task(client, auth_admin, proj["id"])

    assert client.get(f"/projects/{proj['id']}", headers=auth_user).status_code == 200, \
        "same-team GET /projects/<id> must return 200"
    assert client.get(f"/projects/{proj['id']}/tasks", headers=auth_user).status_code == 200, \
        "same-team GET /projects/<id>/tasks must return 200"
    assert client.get(f"/tasks/{task['id']}", headers=auth_user).status_code == 200, \
        "same-team GET /tasks/<id> must return 200"


# ── Same-team write access not broken ───────────────────────────────────────

def test_same_team_write_access_not_broken(client, auth_admin, auth_user, two_teams):
    """A non-admin participant must still create tasks, comments, and attachments."""
    proj = _project(client, auth_admin, two_teams["alpha"])

    task_resp = client.post(f"/projects/{proj['id']}/tasks", headers=auth_user, json={
        "title": "alice-task", "description": "my task", "priority": "high",
    })
    assert task_resp.status_code == 200, "same-team task creation must return 200"
    task = task_resp.get_json()

    comment_resp = client.post(f"/tasks/{task['id']}/comments", headers=auth_user,
                               json={"body": "looks good!"})
    assert comment_resp.status_code == 200, "same-team comment creation must return 200"

    attach_resp = client.post(f"/tasks/{task['id']}/attachments", headers=auth_user, json={
        "filename": "design.png",
        "content_b64": base64.b64encode(b"PNG_FAKE_DATA").decode(),
    })
    assert attach_resp.status_code == 200, "same-team attachment upload must return 200"


# ── Project action endpoints not broken for same-team ───────────────────────

def test_same_team_project_actions_not_broken(client, auth_admin, auth_user, two_teams):
    """Non-admin participants must still be able to duplicate, share, and export
    projects belonging to their own team."""
    proj = _project(client, auth_admin, two_teams["alpha"])

    dup = client.post(f"/projects/{proj['id']}/duplicate",
                      headers=auth_user, json={"new_name": "fork"})
    assert dup.status_code == 200, "same-team duplicate must return 200"

    share = client.post(f"/projects/{proj['id']}/share", headers=auth_user)
    assert share.status_code == 200, "same-team share must return 200"

    exp = client.get(f"/projects/{proj['id']}/export", headers=auth_user)
    assert exp.status_code == 200, "same-team export must return 200"
