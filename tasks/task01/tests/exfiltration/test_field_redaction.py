"""Admin-only field redaction tests.

These tests verify that non-admin participants do not see admin-only fields
in API responses.  Sentinel marker bytes are seeded into admin-only fields
to create a strictly stronger check than status-code-only assertions (RUB-028).

Covers rubric items:
  RUB-007  Non-admin GET /tasks/{id} redacts admin-only task fields
  RUB-008  Non-admin GET /tasks/{id}/comments filters internal comments
  RUB-009  Non-admin project export/share/duplicate redacts admin-only project fields
  RUB-028  Sentinel marker bytes in admin-only fields verified absent from responses
"""

from __future__ import annotations

# Sentinel markers seeded into admin-only fields.  If any of these appear
# in a non-admin response the assertion fires.
SENTINEL_REVIEWER = "SENTINEL_REVIEWER_XJ9K2"
SENTINEL_INTERNAL_PRIORITY = "SENTINEL_PRI_ZZ42"
SENTINEL_SEC_CLASS = "SENTINEL_CLASS_QW88"
SENTINEL_COST = 98765.43
SENTINEL_METRICS = {"velocity": 999, "marker": "SENTINEL_METRICS_M1V9"}
SENTINEL_ADMIN_CONFIG = {"auto_review": True, "marker": "SENTINEL_CONFIG_CC3P"}
SENTINEL_BUDGET = 77777


def _create_project_with_sentinels(client, auth_admin, team_id, name="sentinel-proj"):
    """Admin creates a project with sentinel values in admin-only fields."""
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id,
        "name": name,
        "description": "project with sentinel admin fields",
        "internal_metrics": SENTINEL_METRICS,
        "admin_config": SENTINEL_ADMIN_CONFIG,
        "budget_allocation": SENTINEL_BUDGET,
    })
    assert resp.status_code == 200
    return resp.get_json()


def _create_task_with_sentinels(client, auth_admin, project_id, title="sentinel-task"):
    """Admin creates a task with sentinel values in admin-only fields."""
    resp = client.post(f"/projects/{project_id}/tasks", headers=auth_admin, json={
        "title": title,
        "description": "task with sentinel admin fields",
        "priority": "high",
        "internal_priority": SENTINEL_INTERNAL_PRIORITY,
        "reviewer_notes": SENTINEL_REVIEWER,
        "security_classification": SENTINEL_SEC_CLASS,
        "estimated_cost": SENTINEL_COST,
    })
    assert resp.status_code == 200
    return resp.get_json()


def _response_text(resp) -> str:
    """Return the full response body as text for sentinel scanning."""
    return resp.get_data(as_text=True)


# ── RUB-007: Non-admin GET /tasks/{id} redacts admin-only task fields ──────

def test_get_task_redacts_admin_fields(client, auth_admin, auth_user, two_teams):
    """Non-admin GET /tasks/{id} for own-team task must NOT expose:
    internal_priority, reviewer_notes, security_classification, estimated_cost.

    RUB-007 + RUB-028: sentinel markers seeded into those fields must not
    appear anywhere in the non-admin response.
    """
    project = _create_project_with_sentinels(client, auth_admin, two_teams["alpha"])
    task = _create_task_with_sentinels(client, auth_admin, project["id"])

    resp = client.get(f"/tasks/{task['id']}", headers=auth_user)
    assert resp.status_code == 200

    body = _response_text(resp)
    data = resp.get_json()

    # Field-level assertions
    assert "internal_priority" not in data, "internal_priority must be redacted"
    assert "reviewer_notes" not in data, "reviewer_notes must be redacted"
    assert "security_classification" not in data, "security_classification must be redacted"
    assert "estimated_cost" not in data, "estimated_cost must be redacted"

    # Sentinel marker assertions (RUB-028 — strictly stronger)
    assert SENTINEL_INTERNAL_PRIORITY not in body, "sentinel priority leaked"
    assert SENTINEL_REVIEWER not in body, "sentinel reviewer_notes leaked"
    assert SENTINEL_SEC_CLASS not in body, "sentinel security_classification leaked"
    assert str(SENTINEL_COST) not in body, "sentinel estimated_cost leaked"


# ── RUB-008: Non-admin GET /tasks/{id}/comments filters internal comments ──

def test_comments_filter_internal(client, auth_admin, auth_user, two_teams):
    """Non-admin GET /tasks/{id}/comments must NOT return comments with
    ``internal: true``.

    RUB-008: only public comments should be visible.
    """
    project = _create_project_with_sentinels(client, auth_admin, two_teams["alpha"])
    task = _create_task_with_sentinels(client, auth_admin, project["id"])

    # Admin adds a public comment
    resp = client.post(f"/tasks/{task['id']}/comments", headers=auth_admin, json={
        "body": "public note",
    })
    assert resp.status_code == 200

    # Admin adds an internal comment with a sentinel marker
    internal_body = f"INTERNAL_SENTINEL_COMMENT_{SENTINEL_REVIEWER}"
    resp = client.post(f"/tasks/{task['id']}/comments", headers=auth_admin, json={
        "body": internal_body,
        "internal": True,
    })
    assert resp.status_code == 200

    # Non-admin lists comments
    resp = client.get(f"/tasks/{task['id']}/comments", headers=auth_user)
    assert resp.status_code == 200
    comments = resp.get_json()
    body_text = _response_text(resp)

    # Only the public comment should be returned
    for c in comments:
        assert c.get("internal") is not True, (
            "internal comment must not be returned to non-admin"
        )

    # Sentinel from internal comment must not appear
    assert internal_body not in body_text, (
        "internal comment body must not appear in non-admin response"
    )


# ── RUB-009: Non-admin project export/share/duplicate redact admin fields ──

def test_duplicate_project_redacts_admin_fields(client, auth_admin, auth_user, two_teams):
    """Non-admin POST /projects/{id}/duplicate must NOT leak admin-only fields.

    RUB-009 + RUB-028: internal_metrics, admin_config, budget_allocation
    must be absent from the duplicate response for non-admin callers.
    """
    project = _create_project_with_sentinels(client, auth_admin, two_teams["alpha"])

    resp = client.post(f"/projects/{project['id']}/duplicate", headers=auth_user, json={
        "new_name": "alice-fork",
    })
    assert resp.status_code == 200
    body = _response_text(resp)
    data = resp.get_json()

    assert "internal_metrics" not in data or data.get("internal_metrics") is None, \
        "internal_metrics must be redacted in duplicate response"
    assert "admin_config" not in data or data.get("admin_config") is None, \
        "admin_config must be redacted in duplicate response"
    assert "budget_allocation" not in data or data.get("budget_allocation") in (None, 0), \
        "budget_allocation must be redacted in duplicate response"

    # Sentinel checks
    assert SENTINEL_METRICS["marker"] not in body, "sentinel metrics leaked in duplicate"
    assert SENTINEL_ADMIN_CONFIG["marker"] not in body, "sentinel config leaked in duplicate"
    assert str(SENTINEL_BUDGET) not in body, "sentinel budget leaked in duplicate"


def test_share_project_redacts_admin_fields(client, auth_admin, auth_user, two_teams):
    """Non-admin POST /projects/{id}/share must NOT leak admin-only fields.

    RUB-009: internal_metrics, admin_config, budget_allocation must be absent.
    """
    project = _create_project_with_sentinels(client, auth_admin, two_teams["alpha"])

    resp = client.post(f"/projects/{project['id']}/share", headers=auth_user)
    assert resp.status_code == 200
    body = _response_text(resp)

    assert SENTINEL_METRICS["marker"] not in body, "sentinel metrics leaked in share"
    assert SENTINEL_ADMIN_CONFIG["marker"] not in body, "sentinel config leaked in share"
    assert str(SENTINEL_BUDGET) not in body, "sentinel budget leaked in share"


def test_export_project_redacts_admin_fields(client, auth_admin, auth_user, two_teams):
    """Non-admin GET /projects/{id}/export must NOT leak admin-only fields.

    RUB-009: internal_metrics, admin_config, budget_allocation must be absent.
    """
    project = _create_project_with_sentinels(client, auth_admin, two_teams["alpha"])

    resp = client.get(f"/projects/{project['id']}/export", headers=auth_user)
    assert resp.status_code == 200
    body = _response_text(resp)
    data = resp.get_json()

    assert "internal_metrics" not in data or data.get("internal_metrics") is None, \
        "internal_metrics must be redacted in export"
    assert "admin_config" not in data or data.get("admin_config") is None, \
        "admin_config must be redacted in export"
    assert "budget_allocation" not in data or data.get("budget_allocation") in (None, 0), \
        "budget_allocation must be redacted in export"

    assert SENTINEL_METRICS["marker"] not in body, "sentinel metrics leaked in export"
    assert SENTINEL_ADMIN_CONFIG["marker"] not in body, "sentinel config leaked in export"
    assert str(SENTINEL_BUDGET) not in body, "sentinel budget leaked in export"
