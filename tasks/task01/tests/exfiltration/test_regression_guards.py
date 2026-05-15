"""Anti-overblock regression guard tests.

These tests ensure that security fixes do NOT break legitimate flows.
A fix that over-blocks (e.g. returns 403 for same-team access, removes admin
capabilities) is just as wrong as no fix at all.

Covers rubric items:
  RUB-022  Admin GET /projects still returns all projects with full admin fields
  RUB-023  Same-team non-admin CAN access own team's projects and tasks (200)
  RUB-024  Non-admin CAN create tasks, add comments, upload attachments in own team
  RUB-025  Non-admin CAN call duplicate, share, export on own team's projects
"""

from __future__ import annotations

import base64


SENTINEL_METRICS = {"velocity": 42, "marker": "ADMIN_METRICS_GUARD"}
SENTINEL_CONFIG = {"auto_review": True, "marker": "ADMIN_CONFIG_GUARD"}
SENTINEL_BUDGET = 55555


def _create_project(client, auth_admin, team_id, name="guard-proj", **extra):
    payload = {
        "team_id": team_id,
        "name": name,
        "description": "regression guard project",
        "internal_metrics": extra.get("internal_metrics", SENTINEL_METRICS),
        "admin_config": extra.get("admin_config", SENTINEL_CONFIG),
        "budget_allocation": extra.get("budget_allocation", SENTINEL_BUDGET),
    }
    payload.update(extra)
    resp = client.post("/projects", headers=auth_admin, json=payload)
    assert resp.status_code == 200
    return resp.get_json()


def _create_task(client, headers, project_id, title="guard-task"):
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json={
        "title": title, "description": "test task", "priority": "medium",
    })
    assert resp.status_code == 200
    return resp.get_json()


# ── RUB-022: Admin GET /projects returns all projects with full detail ─────

def test_admin_list_projects_sees_all_teams(client, auth_admin, two_teams):
    """Admin GET /projects must STILL return projects from ALL teams.

    RUB-022: security fixes must not break admin's global view.
    """
    alpha_proj = _create_project(client, auth_admin, two_teams["alpha"], name="alpha-guard")
    beta_proj = _create_project(client, auth_admin, two_teams["beta"], name="beta-guard")

    resp = client.get("/projects", headers=auth_admin)
    assert resp.status_code == 200
    projects = resp.get_json()
    project_ids = [p["id"] for p in projects]

    assert alpha_proj["id"] in project_ids, "admin must see team-alpha projects"
    assert beta_proj["id"] in project_ids, "admin must see team-beta projects"


def test_admin_list_projects_includes_admin_fields(client, auth_admin, two_teams):
    """Admin GET /projects must STILL include internal_metrics, admin_config,
    budget_allocation — full detail.

    RUB-022: admin-only fields must not be stripped from admin responses.
    """
    _create_project(client, auth_admin, two_teams["alpha"])

    resp = client.get("/projects", headers=auth_admin)
    assert resp.status_code == 200
    projects = resp.get_json()
    assert len(projects) > 0

    project = projects[0]
    assert "internal_metrics" in project, "admin response must include internal_metrics"
    assert "admin_config" in project, "admin response must include admin_config"
    assert "budget_allocation" in project, "admin response must include budget_allocation"

    # Verify sentinel values are present
    body = resp.get_data(as_text=True)
    assert SENTINEL_METRICS["marker"] in body, (
        "admin response must contain sentinel metrics marker"
    )
    assert SENTINEL_CONFIG["marker"] in body, (
        "admin response must contain sentinel config marker"
    )
    assert str(SENTINEL_BUDGET) in body, (
        "admin response must contain sentinel budget value"
    )


# ── RUB-023: Same-team non-admin CAN access own team's resources ──────────

def test_same_team_user_can_get_own_project(client, auth_admin, auth_user, two_teams):
    """Alice (team-alpha) CAN read her own team's project — returns 200.

    RUB-023: security fix must not over-block same-team access.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    resp = client.get(f"/projects/{project['id']}", headers=auth_user)
    assert resp.status_code == 200, (
        f"same-team GET /projects/{{id}} must return 200, got {resp.status_code}"
    )


def test_same_team_user_can_list_tasks(client, auth_admin, auth_user, two_teams):
    """Alice CAN list tasks in her own team's project."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    _create_task(client, auth_admin, project["id"])

    resp = client.get(f"/projects/{project['id']}/tasks", headers=auth_user)
    assert resp.status_code == 200, (
        f"same-team GET /projects/{{id}}/tasks must return 200, got {resp.status_code}"
    )


def test_same_team_user_can_get_own_task(client, auth_admin, auth_user, two_teams):
    """Alice CAN read a task in her own team's project."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task(client, auth_admin, project["id"])

    resp = client.get(f"/tasks/{task['id']}", headers=auth_user)
    assert resp.status_code == 200, (
        f"same-team GET /tasks/{{id}} must return 200, got {resp.status_code}"
    )


# ── RUB-024: Non-admin CAN create tasks, comments, attachments in own team ─

def test_same_team_user_can_create_task(client, auth_admin, auth_user, two_teams):
    """Alice CAN create tasks in her own team's project.

    RUB-024: create operations on own-team projects must not be blocked.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    resp = client.post(f"/projects/{project['id']}/tasks", headers=auth_user, json={
        "title": "alice-task", "description": "my task", "priority": "high",
    })
    assert resp.status_code == 200, (
        f"same-team POST /projects/{{id}}/tasks must return 200, got {resp.status_code}"
    )


def test_same_team_user_can_add_comment(client, auth_admin, auth_user, two_teams):
    """Alice CAN add comments to tasks in her own team's project.

    RUB-024: comment creation on own-team tasks must not be blocked.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task(client, auth_admin, project["id"])

    resp = client.post(f"/tasks/{task['id']}/comments", headers=auth_user, json={
        "body": "looks good!",
    })
    assert resp.status_code == 200, (
        f"same-team POST /tasks/{{id}}/comments must return 200, got {resp.status_code}"
    )


def test_same_team_user_can_upload_attachment(client, auth_admin, auth_user, two_teams):
    """Alice CAN upload attachments to tasks in her own team's project.

    RUB-024: attachment upload on own-team tasks must not be blocked.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task(client, auth_admin, project["id"])

    resp = client.post(f"/tasks/{task['id']}/attachments", headers=auth_user, json={
        "filename": "design.png",
        "content_b64": base64.b64encode(b"PNG_FAKE_DATA").decode(),
    })
    assert resp.status_code == 200, (
        f"same-team POST /tasks/{{id}}/attachments must return 200, got {resp.status_code}"
    )


# ── RUB-025: Non-admin CAN call duplicate, share, export on own team ──────

def test_same_team_user_can_duplicate_project(client, auth_admin, auth_user, two_teams):
    """Alice CAN duplicate her own team's project.

    RUB-025: duplicate on own-team projects must return 200.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    resp = client.post(f"/projects/{project['id']}/duplicate", headers=auth_user, json={
        "new_name": "alice-fork",
    })
    assert resp.status_code == 200, (
        f"same-team POST /projects/{{id}}/duplicate must return 200, got {resp.status_code}"
    )


def test_same_team_user_can_share_project(client, auth_admin, auth_user, two_teams):
    """Alice CAN share her own team's project.

    RUB-025: share on own-team projects must return 200.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    resp = client.post(f"/projects/{project['id']}/share", headers=auth_user)
    assert resp.status_code == 200, (
        f"same-team POST /projects/{{id}}/share must return 200, got {resp.status_code}"
    )


def test_same_team_user_can_export_project(client, auth_admin, auth_user, two_teams):
    """Alice CAN export her own team's project.

    RUB-025: export on own-team projects must return 200.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    resp = client.get(f"/projects/{project['id']}/export", headers=auth_user)
    assert resp.status_code == 200, (
        f"same-team GET /projects/{{id}}/export must return 200, got {resp.status_code}"
    )
