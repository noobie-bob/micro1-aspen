"""Required regression and boundary tests derived from validated success findings."""

from __future__ import annotations

import pytest

from .helpers import call_tool_capture, create_project, create_task


@pytest.mark.asyncio
async def test_same_team_non_admin_lifecycle_stays_usable(mcp_client, auth_user, two_teams):
    """RUB-027: legitimate same-team lifecycle flows must remain functional."""
    project_id = await create_project(
        mcp_client,
        auth_user,
        two_teams["alpha"],
        "alpha-regression-flow",
        "regression guard",
    )

    task_id = await create_task(mcp_client, auth_user, project_id, "initial title")

    ok_update, update_payload = await call_tool_capture(
        mcp_client,
        "update_task",
        {
            "token": auth_user,
            "task_id": task_id,
            "title": "updated title",
            "priority": "low",
        },
    )
    assert ok_update, f"same-team update_task should succeed: {update_payload}"
    assert update_payload.get("title") == "updated title", f"update_task title mismatch: {update_payload}"
    assert update_payload.get("priority") == "low", f"update_task priority mismatch: {update_payload}"

    ok_comment, comment_payload = await call_tool_capture(
        mcp_client,
        "add_comment",
        {
            "token": auth_user,
            "task_id": task_id,
            "body": "alpha lifecycle comment",
            "internal": False,
        },
    )
    assert ok_comment, f"same-team add_comment should succeed: {comment_payload}"

    ok_list, list_payload = await call_tool_capture(
        mcp_client,
        "list_task_comments",
        {"token": auth_user, "task_id": task_id},
    )
    assert ok_list, f"same-team list_task_comments should succeed: {list_payload}"
    assert isinstance(list_payload, list), f"comment list must be a list: {list_payload}"
    assert any(c.get("body") == "alpha lifecycle comment" for c in list_payload), (
        f"comment body not found in list response: {list_payload}"
    )


@pytest.mark.asyncio
async def test_cross_team_search_isolation_with_in_scope_control(
    mcp_client,
    auth_admin,
    auth_user,
    two_teams,
):
    """RUB-029: out-of-scope results must not leak while in-scope control query still works."""
    alpha_project = await create_project(
        mcp_client,
        auth_admin,
        two_teams["alpha"],
        "alpha-search-project",
        "scope test",
    )
    beta_project = await create_project(
        mcp_client,
        auth_admin,
        two_teams["beta"],
        "beta-search-project",
        "scope test",
    )

    alpha_title = "alpha shared-leak-marker control-alpha-only"
    beta_title = "beta shared-leak-marker control-beta-only"

    await create_task(mcp_client, auth_admin, alpha_project, alpha_title)
    await create_task(mcp_client, auth_admin, beta_project, beta_title)

    ok_shared, shared_payload = await call_tool_capture(
        mcp_client,
        "search_tasks",
        {"token": auth_user, "q": "shared-leak-marker"},
    )
    assert ok_shared, f"shared search call failed: {shared_payload}"
    assert isinstance(shared_payload, list), f"search payload must be list: {shared_payload}"

    shared_titles = [t.get("title", "") for t in shared_payload]
    assert alpha_title in shared_titles, f"in-scope task missing from search results: {shared_titles}"
    assert beta_title not in shared_titles, f"cross-team task leaked in shared query: {shared_titles}"

    ok_control, control_payload = await call_tool_capture(
        mcp_client,
        "search_tasks",
        {"token": auth_user, "q": "control-alpha-only"},
    )
    assert ok_control, f"control search call failed: {control_payload}"
    assert isinstance(control_payload, list), f"control search payload must be list: {control_payload}"

    control_titles = [t.get("title", "") for t in control_payload]
    assert control_titles == [alpha_title], (
        "in-scope control query must return exactly the alpha task; "
        f"got {control_titles}"
    )
