"""Mass assignment tests.

Covers rubric items:
  RUB-017  Non-admin PATCH /tasks/{id} cannot overwrite admin-only task fields
  RUB-018  Non-admin PATCH /projects/{id} cannot overwrite admin-only project fields
"""

from __future__ import annotations


def _create_project(client, auth_admin, team_id, name="proj", **extra):
    payload = {"team_id": team_id, "name": name, "description": "test"}
    payload.update(extra)
    resp = client.post("/projects", headers=auth_admin, json=payload)
    assert resp.status_code == 200
    return resp.get_json()


def _create_task(client, headers, project_id, title="task"):
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json={
        "title": title, "description": "test", "priority": "medium",
        "internal_priority": "P2",
        "reviewer_notes": "original notes",
        "security_classification": "public",
        "estimated_cost": 100.0,
    })
    assert resp.status_code == 200
    return resp.get_json()


# ── RUB-017: Non-admin PATCH /tasks/{id} mass assignment ──────────────────

def test_patch_task_mass_assignment_internal_priority(client, auth_admin, auth_user, two_teams):
    """Non-admin PATCH /tasks/{id} must not overwrite internal_priority.

    RUB-017: mass assignment of privileged fields must be rejected or ignored.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task(client, auth_admin, project["id"])
    original_priority = task["internal_priority"]

    resp = client.patch(f"/tasks/{task['id']}", headers=auth_user, json={
        "internal_priority": "P0-ESCALATED",
    })
    # Should either reject (403/400) or silently ignore the field
    if resp.status_code == 200:
        data = resp.get_json()
        assert data.get("internal_priority") == original_priority, (
            "non-admin must not be able to overwrite internal_priority"
        )
    else:
        assert resp.status_code in (400, 403)


def test_patch_task_mass_assignment_reviewer_notes(client, auth_admin, auth_user, two_teams):
    """Non-admin must not overwrite reviewer_notes via mass assignment."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task(client, auth_admin, project["id"])
    original_notes = task["reviewer_notes"]

    resp = client.patch(f"/tasks/{task['id']}", headers=auth_user, json={
        "reviewer_notes": "INJECTED_BY_ATTACKER",
    })
    if resp.status_code == 200:
        data = resp.get_json()
        assert data.get("reviewer_notes") == original_notes, (
            "non-admin must not be able to overwrite reviewer_notes"
        )
    else:
        assert resp.status_code in (400, 403)


def test_patch_task_mass_assignment_security_classification(client, auth_admin, auth_user, two_teams):
    """Non-admin must not overwrite security_classification."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task(client, auth_admin, project["id"])

    resp = client.patch(f"/tasks/{task['id']}", headers=auth_user, json={
        "security_classification": "top-secret",
    })
    if resp.status_code == 200:
        data = resp.get_json()
        assert data.get("security_classification") != "top-secret", (
            "non-admin must not be able to overwrite security_classification"
        )
    else:
        assert resp.status_code in (400, 403)


def test_patch_task_mass_assignment_estimated_cost(client, auth_admin, auth_user, two_teams):
    """Non-admin must not overwrite estimated_cost."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    task = _create_task(client, auth_admin, project["id"])
    original_cost = task["estimated_cost"]

    resp = client.patch(f"/tasks/{task['id']}", headers=auth_user, json={
        "estimated_cost": 999999.99,
    })
    if resp.status_code == 200:
        data = resp.get_json()
        assert data.get("estimated_cost") == original_cost, (
            "non-admin must not be able to overwrite estimated_cost"
        )
    else:
        assert resp.status_code in (400, 403)


# ── RUB-018: Non-admin PATCH /projects/{id} mass assignment ───────────────

def test_patch_project_mass_assignment_internal_metrics(client, auth_admin, auth_user, two_teams):
    """Non-admin PATCH /projects/{id} must not overwrite internal_metrics.

    RUB-018: mass assignment of admin-only project fields must be rejected
    or ignored.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"],
                              internal_metrics={"velocity": 10, "risk_score": "low"})
    original_metrics = project["internal_metrics"]

    resp = client.patch(f"/projects/{project['id']}", headers=auth_user, json={
        "internal_metrics": {"velocity": 9999, "risk_score": "critical"},
    })
    if resp.status_code == 200:
        data = resp.get_json()
        assert data.get("internal_metrics") == original_metrics, (
            "non-admin must not be able to overwrite internal_metrics"
        )
    else:
        assert resp.status_code in (400, 403)


def test_patch_project_mass_assignment_admin_config(client, auth_admin, auth_user, two_teams):
    """Non-admin must not overwrite admin_config."""
    project = _create_project(client, auth_admin, two_teams["alpha"],
                              admin_config={"auto_review": False, "compliance_tier": "standard"})
    original_config = project["admin_config"]

    resp = client.patch(f"/projects/{project['id']}", headers=auth_user, json={
        "admin_config": {"auto_review": True, "compliance_tier": "none"},
    })
    if resp.status_code == 200:
        data = resp.get_json()
        assert data.get("admin_config") == original_config, (
            "non-admin must not be able to overwrite admin_config"
        )
    else:
        assert resp.status_code in (400, 403)


def test_patch_project_mass_assignment_budget(client, auth_admin, auth_user, two_teams):
    """Non-admin must not overwrite budget_allocation."""
    project = _create_project(client, auth_admin, two_teams["alpha"],
                              budget_allocation=5000)
    original_budget = project["budget_allocation"]

    resp = client.patch(f"/projects/{project['id']}", headers=auth_user, json={
        "budget_allocation": 999999,
    })
    if resp.status_code == 200:
        data = resp.get_json()
        assert data.get("budget_allocation") == original_budget, (
            "non-admin must not be able to overwrite budget_allocation"
        )
    else:
        assert resp.status_code in (400, 403)
