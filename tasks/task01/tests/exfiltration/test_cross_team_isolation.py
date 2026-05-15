"""Cross-team data isolation tests.

These tests verify that non-admin participants cannot access resources
belonging to teams they are not members of.

Covers rubric items:
  RUB-001  Non-admin GET /projects returns only caller's team projects
  RUB-002  Non-admin GET /projects/{id} returns 403/404 for cross-team project
  RUB-003  Non-admin GET /projects/{id}/tasks returns 403/404 for cross-team project
  RUB-004  Non-admin GET /tasks/{id} returns 403/404 for cross-team task
  RUB-005  Non-admin PATCH /tasks/{id} returns 403 for cross-team task
  RUB-006  Non-admin DELETE /tasks/{id} returns 403 for cross-team task
"""

from __future__ import annotations

import base64


def _create_project(client, auth_admin, team_id, name="proj", **extra):
    """Admin creates a project under a team, with optional extra fields."""
    payload = {"team_id": team_id, "name": name, "description": "test"}
    payload.update(extra)
    resp = client.post("/projects", headers=auth_admin, json=payload)
    assert resp.status_code == 200
    return resp.get_json()


def _create_task(client, headers, project_id, title="task", **extra):
    """Create a task in a project."""
    payload = {"title": title, "description": "test task", "priority": "medium"}
    payload.update(extra)
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json=payload)
    assert resp.status_code == 200
    return resp.get_json()


# ── RUB-001: Non-admin GET /projects list returns only own-team projects ────

def test_list_projects_returns_only_own_team(client, auth_admin, auth_user, auth_user2, two_teams):
    """Alice (team-alpha) listing projects must NOT see team-beta projects.

    RUB-001: A test asserts that a non-admin GET /projects (list endpoint)
    returns only projects belonging to the caller's team, not projects from
    other teams.
    """
    # Admin creates one project per team
    alpha_proj = _create_project(client, auth_admin, two_teams["alpha"], name="alpha-secret")
    beta_proj = _create_project(client, auth_admin, two_teams["beta"], name="beta-secret")

    # Alice (team-alpha member) lists projects
    resp = client.get("/projects", headers=auth_user)
    assert resp.status_code == 200
    projects = resp.get_json()
    project_ids = [p["id"] for p in projects]

    # Alice must see her own team's project
    assert alpha_proj["id"] in project_ids, "own-team project must be visible"
    # Alice must NOT see the other team's project
    assert beta_proj["id"] not in project_ids, (
        "cross-team project must NOT appear in non-admin listing"
    )


def test_list_projects_bob_sees_only_beta(client, auth_admin, auth_user2, two_teams):
    """Bob (team-beta) listing projects must NOT see team-alpha projects."""
    alpha_proj = _create_project(client, auth_admin, two_teams["alpha"], name="alpha-only")
    beta_proj = _create_project(client, auth_admin, two_teams["beta"], name="beta-only")

    resp = client.get("/projects", headers=auth_user2)
    assert resp.status_code == 200
    projects = resp.get_json()
    project_ids = [p["id"] for p in projects]

    assert beta_proj["id"] in project_ids
    assert alpha_proj["id"] not in project_ids, (
        "Bob must NOT see team-alpha projects"
    )


# ── RUB-002: Non-admin GET /projects/{id} for cross-team project ───────────

def test_get_project_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Alice must not be able to read a team-beta project by ID.

    RUB-002: A test asserts that a non-admin GET /projects/{id} returns a
    403 (or 404) for a project belonging to a different team.
    """
    beta_proj = _create_project(client, auth_admin, two_teams["beta"], name="beta-classified")

    resp = client.get(f"/projects/{beta_proj['id']}", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"cross-team GET /projects/{{id}} must return 403 or 404, got {resp.status_code}"
    )


def test_get_project_own_team_allowed(client, auth_admin, auth_user, two_teams):
    """Alice CAN read her own team's project (sanity check)."""
    alpha_proj = _create_project(client, auth_admin, two_teams["alpha"], name="alpha-readable")
    resp = client.get(f"/projects/{alpha_proj['id']}", headers=auth_user)
    assert resp.status_code == 200


# ── RUB-003: Non-admin GET /projects/{id}/tasks cross-team ─────────────────

def test_list_tasks_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Alice must not list tasks in a team-beta project.

    RUB-003: A test asserts that a non-admin GET /projects/{id}/tasks
    returns a 403 (or 404) for a project belonging to a different team.
    """
    beta_proj = _create_project(client, auth_admin, two_teams["beta"])
    _create_task(client, auth_admin, beta_proj["id"], title="secret-task")

    resp = client.get(f"/projects/{beta_proj['id']}/tasks", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"cross-team GET /projects/{{id}}/tasks must return 403/404, got {resp.status_code}"
    )


# ── RUB-004: Non-admin GET /tasks/{id} cross-team ─────────────────────────

def test_get_task_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Alice must not read a task belonging to a team-beta project.

    RUB-004: A test asserts that a non-admin GET /tasks/{id} returns a
    403 (or 404) for a task belonging to a cross-team project.
    """
    beta_proj = _create_project(client, auth_admin, two_teams["beta"])
    beta_task = _create_task(client, auth_admin, beta_proj["id"], title="hidden-task")

    resp = client.get(f"/tasks/{beta_task['id']}", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"cross-team GET /tasks/{{id}} must return 403/404, got {resp.status_code}"
    )


# ── RUB-005: Non-admin PATCH /tasks/{id} cross-team ───────────────────────

def test_patch_task_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Alice must not be able to modify a task in a team-beta project.

    RUB-005: A test asserts that a non-admin PATCH /tasks/{id} returns a
    403 for a task in a cross-team project, preventing unauthorized
    modification.
    """
    beta_proj = _create_project(client, auth_admin, two_teams["beta"])
    beta_task = _create_task(client, auth_admin, beta_proj["id"])

    resp = client.patch(f"/tasks/{beta_task['id']}", headers=auth_user, json={
        "title": "hacked-title",
    })
    assert resp.status_code == 403, (
        f"cross-team PATCH /tasks/{{id}} must return 403, got {resp.status_code}"
    )


# ── RUB-006: Non-admin DELETE /tasks/{id} cross-team ──────────────────────

def test_delete_task_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Alice must not be able to delete a task in a team-beta project.

    RUB-006: A test asserts that a non-admin DELETE /tasks/{id} returns a
    403 for a task in a cross-team project, preventing unauthorized deletion.
    """
    beta_proj = _create_project(client, auth_admin, two_teams["beta"])
    beta_task = _create_task(client, auth_admin, beta_proj["id"])

    resp = client.delete(f"/tasks/{beta_task['id']}", headers=auth_user)
    assert resp.status_code == 403, (
        f"cross-team DELETE /tasks/{{id}} must return 403, got {resp.status_code}"
    )
