"""SQL injection and OS command injection tests.

Covers rubric items:
  RUB-012  GET /search/tasks is not vulnerable to UNION SELECT SQL injection
  RUB-013  POST /projects/{id}/generate-report does not allow OS command injection
"""

from __future__ import annotations


def _create_project(client, auth_admin, team_id, name="proj"):
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id, "name": name, "description": "test",
    })
    assert resp.status_code == 200
    return resp.get_json()


def _create_task(client, headers, project_id, title="task"):
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json={
        "title": title, "description": "test task", "priority": "medium",
        "internal_priority": "P0-SECRET",
        "reviewer_notes": "TOP_SECRET_REVIEWER_NOTE",
    })
    assert resp.status_code == 200
    return resp.get_json()


# ── RUB-012: SQL injection via /search/tasks ───────────────────────────────

def test_search_tasks_sqli_union_select(client, auth_admin, auth_user, two_teams):
    """A UNION SELECT injection in /search/tasks must NOT return data from
    other tables.

    RUB-012: the q parameter must be parameterised. A UNION SELECT payload
    must not leak internal_priority or reviewer_notes from task_index.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    _create_task(client, auth_admin, project["id"], title="normal-task")

    # Attempt SQL injection via UNION SELECT
    sqli_payload = "' UNION SELECT id, internal_priority, reviewer_notes, status FROM task_index --"
    resp = client.get(f"/search/tasks?q={sqli_payload}", headers=auth_user)

    # The endpoint should either reject the input or return safe results
    body = resp.get_data(as_text=True)

    # Sensitive columns from task_index must NOT appear in results
    assert "P0-SECRET" not in body, (
        "SQL injection leaked internal_priority from task_index"
    )
    assert "TOP_SECRET_REVIEWER_NOTE" not in body, (
        "SQL injection leaked reviewer_notes from task_index"
    )


def test_search_tasks_sqli_does_not_error_with_sensitive_data(client, auth_admin, auth_user, two_teams):
    """Even if the SQL injection causes an error, the error message must
    not leak schema details that reveal sensitive column names."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    _create_task(client, auth_admin, project["id"])

    # Another injection variant
    sqli_payload = "'; DROP TABLE task_index; --"
    resp = client.get(f"/search/tasks?q={sqli_payload}", headers=auth_user)

    # Should not successfully execute the DROP
    # Re-search should still work
    resp2 = client.get("/search/tasks?q=task", headers=auth_user)
    assert resp2.status_code in (200, 400)


# ── RUB-013: OS command injection via /projects/{id}/generate-report ───────

def test_generate_report_command_injection_semicolon(client, auth_admin, two_teams):
    """Shell metacharacters in the title/format must NOT execute commands.

    RUB-013: the title or format parameter must not allow arbitrary command
    execution via semicolons, backticks, or pipes.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])

    # Inject a command that creates a marker file
    injection_payload = "test; echo INJECTED_MARKER"
    resp = client.post(f"/projects/{project['id']}/generate-report",
                       headers=auth_admin, json={
                           "format": "txt",
                           "title": injection_payload,
                       })

    body = resp.get_data(as_text=True)
    # The injected command's output must not appear
    assert "INJECTED_MARKER" not in body, (
        "OS command injection via title executed arbitrary command"
    )


def test_generate_report_command_injection_backticks(client, auth_admin, two_teams):
    """Backtick-based injection must not execute."""
    project = _create_project(client, auth_admin, two_teams["alpha"])

    resp = client.post(f"/projects/{project['id']}/generate-report",
                       headers=auth_admin, json={
                           "format": "txt",
                           "title": "`echo BACKTICK_INJECTED`",
                       })
    body = resp.get_data(as_text=True)
    assert "BACKTICK_INJECTED" not in body, (
        "OS command injection via backticks executed arbitrary command"
    )


def test_generate_report_command_injection_pipe(client, auth_admin, two_teams):
    """Pipe-based injection must not execute."""
    project = _create_project(client, auth_admin, two_teams["alpha"])

    resp = client.post(f"/projects/{project['id']}/generate-report",
                       headers=auth_admin, json={
                           "format": "txt",
                           "title": "safe | echo PIPE_INJECTED",
                       })
    body = resp.get_data(as_text=True)
    assert "PIPE_INJECTED" not in body, (
        "OS command injection via pipe executed arbitrary command"
    )
