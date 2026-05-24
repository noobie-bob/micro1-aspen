from __future__ import annotations


def test_participant_reads_own_boundary_project(tool, auth_user):
    project = tool(
        "get_project",
        {"token": auth_user, "project_id": "project-alpha"},
    )
    assert project["id"] == "project-alpha"


def test_participant_discovers_own_boundary_task(tool, auth_user):
    results = tool(
        "search_tasks",
        {"token": auth_user, "q": "SENTINEL_ALPHA_TASK"},
    )
    assert any(task["id"] == "task-alpha" for task in results)


def test_admin_reads_other_boundary_project(tool, auth_admin):
    project = tool(
        "get_project",
        {"token": auth_admin, "project_id": "project-beta"},
    )
    assert project["id"] == "project-beta"


def test_second_participant_reads_own_boundary_comments(tool, auth_user2):
    comments = tool(
        "list_task_comments",
        {"token": auth_user2, "task_id": "task-beta"},
    )
    assert any(comment["task_id"] == "task-beta" for comment in comments)
