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


def _task_with_fields(client, headers, project_id, **extra):
    payload = {
        "title": "baseline-task",
        "description": "baseline",
        "priority": "medium",
        "internal_priority": "P0-TOP-SECRET",
        "reviewer_notes": "EYES-ONLY-REVIEWER-NOTE",
    }
    payload.update(extra)
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json=payload)
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


def test_crafted_search_queries_preserve_scoped_visibility(client, auth_admin, auth_user, two_teams):
    """Crafted search queries must not widen visible resources across either discovery surface.

    Same-boundary benign queries must still work so the test distinguishes
    query hardening from simply breaking search.
    """
    alpha_proj = _project(client, auth_admin, two_teams["alpha"], name="alpha-visible")
    beta_proj = _project(client, auth_admin, two_teams["beta"], name="beta-hidden")
    alpha_task = _task_with_fields(
        client,
        auth_admin,
        alpha_proj["id"],
        title="alpha-findable",
        description="alpha-search-doc",
    )
    beta_task = _task_with_fields(
        client,
        auth_admin,
        beta_proj["id"],
        title="beta-hidden-task",
        description="beta-search-doc",
    )

    benign_projects = client.get(
        "/search/projects",
        headers=auth_user,
        query_string={"q": "alpha-visible"},
    )
    assert benign_projects.status_code == 200
    benign_project_ids = [project["id"] for project in benign_projects.get_json()]
    assert alpha_proj["id"] in benign_project_ids
    assert beta_proj["id"] not in benign_project_ids

    benign_tasks = client.get(
        "/search/tasks",
        headers=auth_user,
        query_string={"q": "alpha-findable"},
    )
    assert benign_tasks.status_code == 200
    benign_task_ids = [task["id"] for task in benign_tasks.get_json()]
    assert alpha_task["id"] in benign_task_ids
    assert beta_task["id"] not in benign_task_ids

    crafted = "' OR 1=1 --"

    project_resp = client.get(
        "/search/projects",
        headers=auth_user,
        query_string={"q": crafted},
    )
    assert project_resp.status_code in (200, 400, 422)
    if project_resp.status_code == 200:
        project_ids = [project["id"] for project in project_resp.get_json()]
        assert alpha_proj["id"] in project_ids
        assert beta_proj["id"] not in project_ids, (
            "crafted project search widened visibility to a foreign project"
        )

    task_resp = client.get(
        "/search/tasks",
        headers=auth_user,
        query_string={"q": crafted},
    )
    assert task_resp.status_code in (200, 400, 422)
    if task_resp.status_code == 200:
        task_ids = [task["id"] for task in task_resp.get_json()]
        assert alpha_task["id"] in task_ids
        assert beta_task["id"] not in task_ids, (
            "crafted task search widened visibility to a foreign task"
        )


def test_crafted_task_search_queries_do_not_extract_restricted_markers(
    client, auth_admin, auth_user, two_teams
):
    """Crafted task searches must not surface restricted indexed metadata.

    A benign query still needs to return the ordinary task result so the test
    preserves normal discovery behaviour while checking raw-body secrecy.
    """
    proj = _project(client, auth_admin, two_teams["alpha"], name="alpha-search-home")
    _task_with_fields(
        client,
        auth_admin,
        proj["id"],
        title="ordinary backlog",
        description="ordinary backlog item",
        internal_priority="P0-TYPEB-SECRET",
        reviewer_notes="TYPEB-REVIEWER-ONLY",
    )

    benign = client.get(
        "/search/tasks",
        headers=auth_user,
        query_string={"q": "ordinary backlog"},
    )
    assert benign.status_code == 200
    benign_body = benign.get_data(as_text=True)
    assert "ordinary backlog" in benign_body
    assert "P0-TYPEB-SECRET" not in benign_body
    assert "TYPEB-REVIEWER-ONLY" not in benign_body

    crafted = "' UNION SELECT id, internal_priority, reviewer_notes, status FROM task_index --"
    injected = client.get(
        "/search/tasks",
        headers=auth_user,
        query_string={"q": crafted},
    )
    assert injected.status_code in (200, 400, 422)
    raw = injected.get_data(as_text=True)
    assert "P0-TYPEB-SECRET" not in raw, (
        "crafted task search exposed restricted priority data"
    )
    assert "TYPEB-REVIEWER-ONLY" not in raw, (
        "crafted task search exposed restricted reviewer notes"
    )


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


def test_generate_report_rejects_shell_breakout_payloads_with_benign_control(
    client, auth_admin, two_teams
):
    """Shell-breakout payloads must not execute while benign report generation still works."""
    proj = _project(client, auth_admin, two_teams["alpha"], name="report-rung")

    benign = client.post(
        f"/projects/{proj['id']}/generate-report",
        headers=auth_admin,
        json={"format": "txt", "title": "quarterly review"},
    )
    assert benign.status_code == 200
    assert "Report: quarterly review" in benign.get_data(as_text=True)

    payloads = [
        ("semicolon", "quarterly review' ; echo TYPEB_CMD_MARKER ; echo '"),
        ("and-and", "quarterly review' && echo TYPEB_CMD_MARKER && echo '"),
        ("newline", "quarterly review'\necho TYPEB_CMD_MARKER\necho '"),
    ]
    for label, payload in payloads:
        resp = client.post(
            f"/projects/{proj['id']}/generate-report",
            headers=auth_admin,
            json={"format": "txt", "title": payload},
        )
        assert resp.status_code in (200, 400, 422, 500)
        assert "TYPEB_CMD_MARKER" not in resp.get_data(as_text=True), (
            f"shell breakout via {label} executed arbitrary command output"
        )
