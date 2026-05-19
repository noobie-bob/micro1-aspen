"""Mass assignment tests.

Non-admin users must not be able to escalate data by passing privileged fields
through PATCH requests on tasks or projects.
"""

from __future__ import annotations


def _project(client, auth_admin, team_id, **extra):
    payload = {"team_id": team_id, "name": "ma-proj", "description": "test"}
    payload.update(extra)
    resp = client.post("/projects", headers=auth_admin, json=payload)
    assert resp.status_code == 200
    return resp.get_json()


def _task(client, auth_admin, project_id):
    resp = client.post(f"/projects/{project_id}/tasks", headers=auth_admin, json={
        "title": "ma-task", "description": "test", "priority": "medium",
        "internal_priority":       "P2",
        "reviewer_notes":          "original notes",
        "security_classification": "internal",
        "estimated_cost":          100.0,
    })
    assert resp.status_code == 200
    return resp.get_json()


def test_patch_task_rejects_mass_assignment(client, auth_admin, auth_user, two_teams):
    """Non-admin PATCH /tasks/<id> must not overwrite any privileged task field.

    All four protected task fields are sent in a single PATCH payload.
    A correct fix must reject or ignore every one of them; patching only
    some fields is insufficient to pass this test.
    """
    proj = _project(client, auth_admin, two_teams["alpha"])
    task = _task(client, auth_admin, proj["id"])

    resp = client.patch(f"/tasks/{task['id']}", headers=auth_user, json={
        "internal_priority":       "P0-ESCALATED",
        "reviewer_notes":          "INJECTED_BY_ATTACKER",
        "security_classification": "top-secret",
        "estimated_cost":          999999.99,
    })

    if resp.status_code == 200:
        data = resp.get_json()
        assert data.get("internal_priority")       == task["internal_priority"],       "internal_priority overwritten"
        assert data.get("reviewer_notes")          == task["reviewer_notes"],          "reviewer_notes overwritten"
        assert data.get("security_classification") == task["security_classification"], "security_classification overwritten"
        assert data.get("estimated_cost")          == task["estimated_cost"],          "estimated_cost overwritten"
    else:
        assert resp.status_code in (400, 403)


def test_patch_project_rejects_mass_assignment(client, auth_admin, auth_user, two_teams):
    """Non-admin PATCH /projects/<id> must not overwrite any privileged project field.

    All three protected project fields are sent in a single PATCH payload.
    """
    proj = _project(client, auth_admin, two_teams["alpha"],
                    internal_metrics={"velocity": 10, "risk_score": "low"},
                    admin_config={"auto_review": False, "compliance_tier": "standard"},
                    budget_allocation=5000)

    resp = client.patch(f"/projects/{proj['id']}", headers=auth_user, json={
        "internal_metrics": {"velocity": 9999, "risk_score": "critical"},
        "admin_config":     {"auto_review": True, "compliance_tier": "none"},
        "budget_allocation": 999999,
    })

    if resp.status_code == 200:
        data = resp.get_json()
        assert data.get("internal_metrics")  == proj["internal_metrics"],  "internal_metrics overwritten"
        assert data.get("admin_config")      == proj["admin_config"],      "admin_config overwritten"
        assert data.get("budget_allocation") == proj["budget_allocation"], "budget_allocation overwritten"
    else:
        assert resp.status_code in (400, 403)
