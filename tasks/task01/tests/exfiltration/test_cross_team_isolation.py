"""Cross-team data isolation tests.

These tests verify that non-admin participants cannot access or mutate
resources belonging to teams they are not members of.
"""

from __future__ import annotations

import base64


def _create_project(client, auth_admin, team_id, name="proj", **extra):
    payload = {"team_id": team_id, "name": name, "description": "test"}
    payload.update(extra)
    resp = client.post("/projects", headers=auth_admin, json=payload)
    assert resp.status_code == 200
    return resp.get_json()


def _create_task(client, headers, project_id, title="task", **extra):
    payload = {"title": title, "description": "test task", "priority": "medium"}
    payload.update(extra)
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json=payload)
    assert resp.status_code == 200
    return resp.get_json()


# ── Cross-team project listing ──────────────────────────────────────────────

def test_list_projects_returns_only_own_team(client, auth_admin, auth_user, auth_user2, two_teams):
    """Non-admin listing /projects must only surface their own team's projects."""
    alpha_proj = _create_project(client, auth_admin, two_teams["alpha"], name="alpha-secret")
    beta_proj  = _create_project(client, auth_admin, two_teams["beta"],  name="beta-secret")

    # Alice (team-alpha) must see her project but NOT beta's
    resp = client.get("/projects", headers=auth_user)
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.get_json()]
    assert alpha_proj["id"] in ids, "own-team project must be visible"
    assert beta_proj["id"] not in ids, "cross-team project must be hidden"

    # Bob (team-beta) must see his project but NOT alpha's
    resp2 = client.get("/projects", headers=auth_user2)
    assert resp2.status_code == 200
    ids2 = [p["id"] for p in resp2.get_json()]
    assert beta_proj["id"] in ids2
    assert alpha_proj["id"] not in ids2, "Bob must not see team-alpha projects"


# ── Cross-team project detail ───────────────────────────────────────────────

def test_get_project_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Non-admin reading /projects/<id> for a cross-team project must get 403/404."""
    beta_proj = _create_project(client, auth_admin, two_teams["beta"], name="beta-classified")

    resp = client.get(f"/projects/{beta_proj['id']}", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"cross-team GET /projects/{{id}} must return 403 or 404, got {resp.status_code}"
    )


def test_get_project_own_team_allowed(client, auth_admin, auth_user, two_teams):
    """Same-team read must still work (anti-overblock)."""
    alpha_proj = _create_project(client, auth_admin, two_teams["alpha"], name="alpha-readable")
    resp = client.get(f"/projects/{alpha_proj['id']}", headers=auth_user)
    assert resp.status_code == 200


# ── Cross-team task listing ─────────────────────────────────────────────────

def test_list_tasks_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Non-admin /projects/<id>/tasks on a cross-team project must return 403/404."""
    beta_proj = _create_project(client, auth_admin, two_teams["beta"])
    _create_task(client, auth_admin, beta_proj["id"], title="secret-task")

    resp = client.get(f"/projects/{beta_proj['id']}/tasks", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"cross-team task list must return 403/404, got {resp.status_code}"
    )


# ── Cross-team task read / write / delete ──────────────────────────────────

def test_get_task_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Non-admin GET /tasks/<id> for a cross-team task must return 403/404."""
    beta_proj = _create_project(client, auth_admin, two_teams["beta"])
    beta_task = _create_task(client, auth_admin, beta_proj["id"], title="hidden-task")

    resp = client.get(f"/tasks/{beta_task['id']}", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"cross-team GET /tasks/{{id}} must return 403/404, got {resp.status_code}"
    )


def test_patch_and_delete_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Non-admin must not mutate (PATCH) or destroy (DELETE) a cross-team task."""
    beta_proj = _create_project(client, auth_admin, two_teams["beta"])
    beta_task = _create_task(client, auth_admin, beta_proj["id"])

    patch_resp = client.patch(f"/tasks/{beta_task['id']}", headers=auth_user,
                              json={"title": "hacked"})
    assert patch_resp.status_code == 403, (
        f"cross-team PATCH must return 403, got {patch_resp.status_code}"
    )

    delete_resp = client.delete(f"/tasks/{beta_task['id']}", headers=auth_user)
    assert delete_resp.status_code == 403, (
        f"cross-team DELETE must return 403, got {delete_resp.status_code}"
    )
