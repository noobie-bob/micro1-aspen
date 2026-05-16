"""Injection security tests — SQL injection and OS command injection."""

from __future__ import annotations


def _project(client, auth_admin, team_id, name="inj-proj"):
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id, "name": name, "description": "test",
    })
    assert resp.status_code == 200
    return resp.get_json()


def _task(client, headers, project_id):
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json={
        "title": "baseline-task",
        "description": "baseline",
        "priority": "medium",
        "internal_priority": "P0-TOP-SECRET",
        "reviewer_notes":    "EYES-ONLY-REVIEWER-NOTE",
    })
    assert resp.status_code == 200
    return resp.get_json()


# ── SQL injection via /search/tasks ─────────────────────────────────────────

def test_search_tasks_not_vulnerable_to_union_injection(client, auth_admin, auth_user, two_teams):
    """A UNION SELECT payload in the search query parameter must not extract
    privileged columns from the underlying search index.

    If the endpoint is vulnerable, the injected SELECT would pull
    privileged fields from the task store into the response body.
    """
    proj = _project(client, auth_admin, two_teams["alpha"])
    _task(client, auth_admin, proj["id"])

    sqli = "' UNION SELECT id, internal_priority, reviewer_notes, status FROM task_index --"
    resp = client.get(f"/search/tasks?q={sqli}", headers=auth_user)
    body = resp.get_data(as_text=True)

    assert "P0-TOP-SECRET"         not in body, "SQL injection leaked internal_priority"
    assert "EYES-ONLY-REVIEWER-NOTE" not in body, "SQL injection leaked reviewer_notes"


# ── OS command injection via /projects/<id>/generate-report ─────────────────

def test_generate_report_rejects_command_injection(client, auth_admin, two_teams):
    """Shell metacharacters in the report title must not execute OS commands.

    Semicolon, backtick, and pipe injection vectors are all attempted; if any
    one of them executes the marker echo command the test fails.
    """
    proj = _project(client, auth_admin, two_teams["alpha"])

    payloads = [
        ("semicolon", "safe; echo INJECTED_MARKER"),
        ("backtick",  "`echo INJECTED_MARKER`"),
        ("pipe",      "safe | echo INJECTED_MARKER"),
    ]
    for label, payload in payloads:
        resp = client.post(f"/projects/{proj['id']}/generate-report",
                           headers=auth_admin,
                           json={"format": "txt", "title": payload})
        body = resp.get_data(as_text=True)
        assert "INJECTED_MARKER" not in body, (
            f"OS command injection via {label} executed arbitrary command"
        )
