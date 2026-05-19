"""Admin-only field redaction tests.

Non-admin participants must not receive privileged metadata in API responses.
Sentinel marker values are seeded into restricted fields to detect data leakage
at the content level — strictly stronger than status-code-only checks.
"""

from __future__ import annotations

# Unique sentinel strings unlikely to appear naturally in responses.
SENTINEL_REVIEWER  = "SENTINEL_REVIEWER_XJ9K2"
SENTINEL_INT_PRI   = "SENTINEL_PRI_ZZ42"
SENTINEL_SEC_CLASS = "SENTINEL_CLASS_QW88"
SENTINEL_COST      = 98765.43
SENTINEL_METRICS   = {"velocity": 999, "marker": "SENTINEL_METRICS_M1V9"}
SENTINEL_CONFIG    = {"auto_review": True, "marker": "SENTINEL_CONFIG_CC3P"}
SENTINEL_BUDGET    = 77777


def _project(client, auth_admin, team_id, name="s-proj"):
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id, "name": name,
        "internal_metrics":  SENTINEL_METRICS,
        "admin_config":      SENTINEL_CONFIG,
        "budget_allocation": SENTINEL_BUDGET,
    })
    assert resp.status_code == 200
    return resp.get_json()


def _task(client, auth_admin, project_id):
    resp = client.post(f"/projects/{project_id}/tasks", headers=auth_admin, json={
        "title": "sentinel-task", "priority": "high",
        "internal_priority":      SENTINEL_INT_PRI,
        "reviewer_notes":         SENTINEL_REVIEWER,
        "security_classification": SENTINEL_SEC_CLASS,
        "estimated_cost":         SENTINEL_COST,
    })
    assert resp.status_code == 200
    return resp.get_json()


def _body(resp) -> str:
    return resp.get_data(as_text=True)


# ── Task field redaction ─────────────────────────────────────────────────────

def test_get_task_redacts_privileged_fields(client, auth_admin, auth_user, two_teams):
    """Non-admin GET /tasks/<id> must not expose any privileged task metadata.

    Both field-key absence and sentinel-value absence are asserted to catch
    partial leakage in 200-OK responses that status codes cannot detect.
    """
    proj = _project(client, auth_admin, two_teams["alpha"])
    task = _task(client, auth_admin, proj["id"])

    resp = client.get(f"/tasks/{task['id']}", headers=auth_user)
    assert resp.status_code == 200
    data = _body(resp)

    assert SENTINEL_INT_PRI   not in data, "privileged priority field leaked"
    assert SENTINEL_REVIEWER  not in data, "reviewer notes leaked"
    assert SENTINEL_SEC_CLASS not in data, "security classification leaked"
    assert str(SENTINEL_COST) not in data, "estimated cost leaked"


# ── Internal comment filtering ──────────────────────────────────────────────

def test_comments_hide_internal_entries(client, auth_admin, auth_user, two_teams):
    """Non-admin GET /tasks/<id>/comments must omit comments marked internal.

    Admin creates both a public and an internal comment; the non-admin caller
    must receive only the public one and must not see the internal body text.
    """
    proj = _project(client, auth_admin, two_teams["alpha"])
    task = _task(client, auth_admin, proj["id"])

    client.post(f"/tasks/{task['id']}/comments", headers=auth_admin,
                json={"body": "public-note"})
    internal_body = f"CLASSIFIED_{SENTINEL_REVIEWER}"
    client.post(f"/tasks/{task['id']}/comments", headers=auth_admin,
                json={"body": internal_body, "internal": True})

    resp = client.get(f"/tasks/{task['id']}/comments", headers=auth_user)
    assert resp.status_code == 200
    raw = _body(resp)

    for comment in resp.get_json():
        assert comment.get("internal") is not True, "internal comment returned to non-admin"
    assert internal_body not in raw, "internal comment body appeared in non-admin response"


# ── Project action endpoint redaction ───────────────────────────────────────

def test_project_action_endpoints_redact_admin_fields(client, auth_admin, auth_user, two_teams):
    """Duplicate, share, and export endpoints must not leak privileged project fields.

    All three secondary channels are exercised in one test so a fix must address
    each of them — fixing only one action endpoint is insufficient.
    """
    proj = _project(client, auth_admin, two_teams["alpha"])

    # duplicate
    dup = client.post(f"/projects/{proj['id']}/duplicate",
                      headers=auth_user, json={"new_name": "fork"})
    assert dup.status_code == 200
    dup_body = _body(dup)
    assert SENTINEL_METRICS["marker"] not in dup_body, "sentinel metrics leaked in duplicate"
    assert SENTINEL_CONFIG["marker"]  not in dup_body, "sentinel config leaked in duplicate"
    assert str(SENTINEL_BUDGET)       not in dup_body, "sentinel budget leaked in duplicate"

    # share
    share = client.post(f"/projects/{proj['id']}/share", headers=auth_user)
    assert share.status_code == 200
    share_body = _body(share)
    assert SENTINEL_METRICS["marker"] not in share_body, "sentinel metrics leaked in share"
    assert SENTINEL_CONFIG["marker"]  not in share_body, "sentinel config leaked in share"
    assert str(SENTINEL_BUDGET)       not in share_body, "sentinel budget leaked in share"

    # export
    exp = client.get(f"/projects/{proj['id']}/export", headers=auth_user)
    assert exp.status_code == 200
    exp_body = _body(exp)
    assert SENTINEL_METRICS["marker"] not in exp_body, "sentinel metrics leaked in export"
    assert SENTINEL_CONFIG["marker"]  not in exp_body, "sentinel config leaked in export"
    assert str(SENTINEL_BUDGET)       not in exp_body, "sentinel budget leaked in export"
