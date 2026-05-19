"""Smoke tests for ProjHub — legitimate participant + admin flows.

These tests encode the codebase's normal-operation surface. They are
load-bearing: the agent uses them to induce how the public API behaves
in legitimate use. They do NOT test for any security issues.
"""

from __future__ import annotations

import base64


def _create_project(client, auth_admin, team_id, name="demo-project"):
    """Helper: admin creates a project under a team."""
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id,
        "name": name,
        "description": "A test project",
    })
    assert resp.status_code == 200
    return resp.get_json()


def _create_task_in_project(client, headers, project_id, title="demo-task"):
    """Helper: create a task in a project."""
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json={
        "title": title,
        "description": "A test task",
        "priority": "high",
    })
    assert resp.status_code == 200
    return resp.get_json()


# ── Health / basic connectivity ─────────────────────────────────────────────

def test_health(client):
    """Non-existent task returns 404, not 500."""
    resp = client.get("/tasks/does-not-exist",
                      headers={"Authorization": "Bearer admin-key"})
    assert resp.status_code != 500


def test_unauthenticated_returns_401(client):
    """Missing auth token yields 401."""
    resp = client.get("/projects")
    assert resp.status_code == 401


# ── Team management (admin) ─────────────────────────────────────────────────

def test_admin_creates_team(client, auth_admin):
    resp = client.post("/teams", headers=auth_admin, json={
        "name": "eng-team",
        "member_ids": ["alice-uuid"],
    })
    assert resp.status_code == 200
    assert resp.get_json()["id"]


def test_admin_adds_member(client, auth_admin, two_teams):
    resp = client.post(
        f"/teams/{two_teams['alpha']}/members",
        headers=auth_admin,
        json={"user_id": "charlie-uuid"},
    )
    assert resp.status_code == 200


# ── Project CRUD (legitimate flows) ────────────────────────────────────────

def test_admin_creates_project(client, auth_admin, two_teams):
    project = _create_project(client, auth_admin, two_teams["alpha"])
    assert project["id"]
    assert project["team_id"] == two_teams["alpha"]


def test_member_creates_project_in_own_team(client, auth_admin, auth_user, two_teams):
    """Alice (team-alpha member) can create a project in team-alpha."""
    resp = client.post("/projects", headers=auth_user, json={
        "team_id": two_teams["alpha"],
        "name": "alice-project",
    })
    assert resp.status_code == 200


def test_member_cannot_create_project_in_other_team(client, auth_user, two_teams):
    """Alice cannot create a project in team-beta."""
    resp = client.post("/projects", headers=auth_user, json={
        "team_id": two_teams["beta"],
        "name": "should-fail",
    })
    assert resp.status_code == 403


# ── Task CRUD (legitimate flows) ───────────────────────────────────────────

def test_member_creates_task_in_own_project(client, auth_admin, auth_user, two_teams):
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task_in_project(client, auth_user, project["id"])
    assert task["id"]


def test_member_updates_own_task(client, auth_admin, auth_user, two_teams):
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task_in_project(client, auth_user, project["id"])
    resp = client.patch(f"/tasks/{task['id']}", headers=auth_user, json={
        "title": "renamed-task",
    })
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "renamed-task"


def test_member_transitions_task(client, auth_admin, auth_user, two_teams):
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task_in_project(client, auth_user, project["id"])
    resp = client.post(f"/tasks/{task['id']}/transition", headers=auth_user, json={
        "status": "in_progress",
    })
    assert resp.status_code == 200


# ── Comments (legitimate flows) ────────────────────────────────────────────

def test_member_adds_comment(client, auth_admin, auth_user, two_teams):
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task_in_project(client, auth_user, project["id"])
    resp = client.post(f"/tasks/{task['id']}/comments", headers=auth_user, json={
        "body": "looks good to me",
    })
    assert resp.status_code == 200


def test_admin_adds_internal_comment(client, auth_admin, two_teams):
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task_in_project(client, auth_admin, project["id"])
    resp = client.post(f"/tasks/{task['id']}/comments", headers=auth_admin, json={
        "body": "internal review note — do not share",
        "internal": True,
    })
    assert resp.status_code == 200
    assert resp.get_json()["internal"] is True


# ── Attachments (legitimate flows) ─────────────────────────────────────────

def test_member_uploads_attachment(client, auth_admin, auth_user, two_teams):
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task_in_project(client, auth_user, project["id"])
    resp = client.post(f"/tasks/{task['id']}/attachments", headers=auth_user, json={
        "filename": "design.png",
        "content_b64": base64.b64encode(b"PNG_FAKE_DATA").decode(),
    })
    assert resp.status_code == 200


def test_member_downloads_own_attachment(client, auth_admin, auth_user, two_teams):
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task_in_project(client, auth_user, project["id"])
    client.post(f"/tasks/{task['id']}/attachments", headers=auth_user, json={
        "filename": "notes.txt",
        "content_b64": base64.b64encode(b"hello world").decode(),
    })
    resp = client.get(f"/tasks/{task['id']}/attachments/notes.txt", headers=auth_user)
    assert resp.status_code == 200


# ── Project duplication, sharing, export (legitimate flows) ─────────────────

def test_member_duplicates_project(client, auth_admin, auth_user, two_teams):
    """Participants legitimately duplicate projects."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    resp = client.post(f"/projects/{project['id']}/duplicate", headers=auth_user,
                       json={"new_name": "alice-fork"})
    assert resp.status_code == 200
    assert resp.get_json()["id"] != project["id"]


def test_member_shares_project(client, auth_admin, auth_user, two_teams):
    """Participants share projects."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    resp = client.post(f"/projects/{project['id']}/share", headers=auth_user)
    assert resp.status_code == 200


def test_member_exports_project(client, auth_admin, auth_user, two_teams):
    """Participants export projects."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    resp = client.get(f"/projects/{project['id']}/export", headers=auth_user)
    assert resp.status_code == 200


# ── Admin endpoints (legitimate flows) ──────────────────────────────────────

def test_admin_views_audit_log(client, auth_admin, two_teams):
    """Admin can view the audit log."""
    resp = client.get("/admin/audit-log", headers=auth_admin)
    assert resp.status_code == 200


def test_admin_views_summary_report(client, auth_admin, two_teams):
    """Admin can view the org summary report."""
    resp = client.get("/admin/reports/summary", headers=auth_admin)
    assert resp.status_code == 200


# ── Search (legitimate flows) ──────────────────────────────────────────────

def test_member_searches_tasks(client, auth_admin, auth_user, two_teams):
    """Participants can search tasks by keyword."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    _create_task_in_project(client, auth_user, project["id"], title="fix login bug")
    resp = client.get("/search/tasks?q=login", headers=auth_user)
    assert resp.status_code == 200


def test_member_searches_projects(client, auth_admin, auth_user, two_teams):
    """Participants can search projects by name."""
    _create_project(client, auth_admin, two_teams["alpha"], name="mobile-app")
    resp = client.get("/search/projects?q=mobile", headers=auth_user)
    assert resp.status_code == 200


# ── Report generation (legitimate flows) ───────────────────────────────────

def test_admin_generates_report(client, auth_admin, two_teams):
    """Admin can generate a project report."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    resp = client.post(f"/projects/{project['id']}/generate-report",
                       headers=auth_admin, json={"format": "txt"})
    assert resp.status_code == 200


# ── Share link (legitimate flows) ──────────────────────────────────────────

def test_member_generates_share_link(client, auth_admin, auth_user, two_teams):
    """Participants can generate share links for projects."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    resp = client.post(f"/projects/{project['id']}/share-link", headers=auth_user)
    assert resp.status_code == 200
    assert resp.get_json()["share_token"]

