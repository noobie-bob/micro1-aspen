"""Smoke tests for ProjHub MCP — legitimate participant + admin flows.

These tests encode the codebase's normal-operation surface. They are
load-bearing: the agent uses them to induce how the API behaves
in legitimate use. They do NOT test for any security issues.
"""

import pytest
import json

# ── Helper functions ────────────────────────────────────────────────────────

async def _create_project(mcp_client, token, team_id, name="demo-project"):
    res = await mcp_client.call_tool("create_project", {
        "token": token, "team_id": team_id, "name": name, "description": "A test project"
    })
    return json.loads(res.content[0].text)["id"]

async def _create_task_in_project(mcp_client, token, project_id, title="demo-task"):
    res = await mcp_client.call_tool("create_task", {
        "token": token, "project_id": project_id, "title": title, "priority": "high"
    })
    return json.loads(res.content[0].text)["id"]

# ── 1. Authentication / Connectivity ────────────────────────────────────────

@pytest.mark.asyncio
async def test_unauthenticated_returns_error(mcp_client):
    """1. Missing auth token yields an error."""
    with pytest.raises(Exception, match="Unauthorized"):
        await mcp_client.call_tool("create_team", {"token": "", "name": "fail", "member_ids": []})

@pytest.mark.asyncio
async def test_invalid_token_returns_error(mcp_client):
    """2. Invalid auth token yields an error."""
    with pytest.raises(Exception, match="Unauthorized"):
        await mcp_client.call_tool("create_team", {"token": "bad-key", "name": "fail", "member_ids": []})

# ── Team management (admin) ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_creates_team(mcp_client, auth_admin):
    """3. Admin successfully creates a team."""
    res = await mcp_client.call_tool("create_team", {
        "token": auth_admin, "name": "eng-team", "member_ids": ["alice-uuid"]
    })
    data = json.loads(res.content[0].text)
    assert data["name"] == "eng-team"
    assert "alice-uuid" in data["member_ids"]
    assert len(data["id"]) > 10

@pytest.mark.asyncio
async def test_user_cannot_create_team(mcp_client, auth_user):
    """4. Non-admin cannot create team."""
    with pytest.raises(Exception, match="Forbidden"):
        await mcp_client.call_tool("create_team", {"token": auth_user, "name": "hack", "member_ids": []})

# ── Project CRUD ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_creates_project(mcp_client, auth_admin, two_teams):
    """5. Admin can create project anywhere."""
    project_id = await _create_project(mcp_client, auth_admin, two_teams["alpha"], "admin-proj")
    assert len(project_id) > 10

@pytest.mark.asyncio
async def test_member_creates_project_in_own_team(mcp_client, auth_user, two_teams):
    """6. Member creates project in own team."""
    res = await mcp_client.call_tool("create_project", {
        "token": auth_user, "team_id": two_teams["alpha"], "name": "alice-project"
    })
    data = json.loads(res.content[0].text)
    assert data["name"] == "alice-project"
    assert data["team_id"] == two_teams["alpha"]

@pytest.mark.asyncio
async def test_member_cannot_create_project_in_other_team(mcp_client, auth_user, two_teams):
    """7. Member cannot create project in other team."""
    with pytest.raises(Exception, match="Forbidden"):
        await mcp_client.call_tool("create_project", {
            "token": auth_user, "team_id": two_teams["beta"], "name": "fail-proj"
        })

@pytest.mark.asyncio
async def test_get_project_legitimate(mcp_client, auth_user, two_teams):
    """8. Fetching an existing project."""
    project_id = await _create_project(mcp_client, auth_user, two_teams["alpha"], "get-me")
    res = await mcp_client.call_tool("get_project", {"token": auth_user, "project_id": project_id})
    data = json.loads(res.content[0].text)
    assert data["id"] == project_id
    assert data["name"] == "get-me"

# ── Task CRUD ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_member_creates_task_in_own_project(mcp_client, auth_admin, auth_user, two_teams):
    """9. Create a task in a project."""
    project_id = await _create_project(mcp_client, auth_admin, two_teams["alpha"])
    task_id = await _create_task_in_project(mcp_client, auth_user, project_id, "fix tests")
    assert len(task_id) > 10

@pytest.mark.asyncio
async def test_update_task_priority(mcp_client, auth_user, two_teams):
    """10. Member updates task priority."""
    project_id = await _create_project(mcp_client, auth_user, two_teams["alpha"])
    task_id = await _create_task_in_project(mcp_client, auth_user, project_id, "T1")
    res = await mcp_client.call_tool("update_task", {
        "token": auth_user, "task_id": task_id, "priority": "low"
    })
    data = json.loads(res.content[0].text)
    assert data["priority"] == "low"

@pytest.mark.asyncio
async def test_delete_task_admin(mcp_client, auth_admin, two_teams):
    """11. Admin deletes a task."""
    project_id = await _create_project(mcp_client, auth_admin, two_teams["alpha"])
    task_id = await _create_task_in_project(mcp_client, auth_admin, project_id, "T1")
    res = await mcp_client.call_tool("delete_task", {"token": auth_admin, "task_id": task_id})
    assert json.loads(res.content[0].text)["status"] == "deleted"
    with pytest.raises(Exception, match="Not Found"):
        await mcp_client.call_tool("update_task", {"token": auth_admin, "task_id": task_id, "title": "gone"})

@pytest.mark.asyncio
async def test_member_cannot_delete_task_in_other_team(mcp_client, auth_admin, auth_user, two_teams):
    """12. Boundary protection on deletion."""
    project_id = await _create_project(mcp_client, auth_admin, two_teams["beta"])
    task_id = await _create_task_in_project(mcp_client, auth_admin, project_id, "T1")
    with pytest.raises(Exception, match="Forbidden"):
        await mcp_client.call_tool("delete_task", {"token": auth_user, "task_id": task_id})

@pytest.mark.asyncio
async def test_member_searches_tasks(mcp_client, auth_user, two_teams):
    """13. Search filters strictly."""
    project_id = await _create_project(mcp_client, auth_user, two_teams["alpha"])
    await _create_task_in_project(mcp_client, auth_user, project_id, "Find this login bug")
    res = await mcp_client.call_tool("search_tasks", {"token": auth_user, "q": "login"})
    data = json.loads(res.content[0].text)
    assert len(data) == 1
    assert data[0]["title"] == "Find this login bug"

# ── Comments ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_member_adds_comment(mcp_client, auth_user, two_teams):
    """14. Member adds normal comment."""
    project_id = await _create_project(mcp_client, auth_user, two_teams["alpha"])
    task_id = await _create_task_in_project(mcp_client, auth_user, project_id)
    res = await mcp_client.call_tool("add_comment", {
        "token": auth_user, "task_id": task_id, "body": "looks good", "internal": False
    })
    data = json.loads(res.content[0].text)
    assert data["body"] == "looks good"
    assert data["internal"] is False

@pytest.mark.asyncio
async def test_admin_adds_internal_comment(mcp_client, auth_admin, two_teams):
    """15. Admin adds internal comment."""
    project_id = await _create_project(mcp_client, auth_admin, two_teams["alpha"])
    task_id = await _create_task_in_project(mcp_client, auth_admin, project_id)
    res = await mcp_client.call_tool("add_comment", {
        "token": auth_admin, "task_id": task_id, "body": "secret", "internal": True
    })
    assert json.loads(res.content[0].text)["internal"] is True

@pytest.mark.asyncio
async def test_member_cannot_add_internal_comment(mcp_client, auth_user, two_teams):
    """16. Strict boundary on internal comments."""
    project_id = await _create_project(mcp_client, auth_user, two_teams["alpha"])
    task_id = await _create_task_in_project(mcp_client, auth_user, project_id)
    with pytest.raises(Exception, match="Only admins can add internal comments"):
        await mcp_client.call_tool("add_comment", {
            "token": auth_user, "task_id": task_id, "body": "secret", "internal": True
        })

@pytest.mark.asyncio
async def test_list_task_comments(mcp_client, auth_admin, two_teams):
    """17. List comments returns accurate counts."""
    project_id = await _create_project(mcp_client, auth_admin, two_teams["alpha"])
    task_id = await _create_task_in_project(mcp_client, auth_admin, project_id)
    await mcp_client.call_tool("add_comment", {"token": auth_admin, "task_id": task_id, "body": "C1"})
    await mcp_client.call_tool("add_comment", {"token": auth_admin, "task_id": task_id, "body": "C2"})
    res = await mcp_client.call_tool("list_task_comments", {"token": auth_admin, "task_id": task_id})
    data = json.loads(res.content[0].text)
    assert len(data) == 2

# ── Integration/Vuln Tool Legitimate Flows ──────────────────────────────────

@pytest.mark.asyncio
async def test_admin_sysinfo(mcp_client):
    """18. Admin sysinfo works correctly."""
    res = await mcp_client.call_tool("admin_sysinfo", {})
    data = json.loads(res.content[0].text)
    assert data["status"] == "healthy"
    assert "os" in data

@pytest.mark.asyncio
async def test_ping_legitimate(mcp_client, auth_user):
    """19. Ping safe target works."""
    res = await mcp_client.call_tool("ping_team_server", {"token": auth_user, "target": "127.0.0.1"})
    data = json.loads(res.content[0].text)
    assert "127.0.0.1" in data["output"] or "localhost" in data["output"]

@pytest.mark.asyncio
async def test_calculate_budget_legitimate(mcp_client, auth_user):
    """20. Math works."""
    res = await mcp_client.call_tool("calculate_budget", {"token": auth_user, "expression": "10 * 5"})
    data = json.loads(res.content[0].text)
    assert data["result"] == 50

@pytest.mark.asyncio
async def test_fetch_project_asset_legitimate(mcp_client, auth_user):
    """21. SSRF mock test works on safe domain."""
    # Since we can't guarantee network access to external sites in some runners, 
    # we expect the tool to catch standard failures and return error json.
    # However, "example.com" should resolve in most environments.
    res = await mcp_client.call_tool("fetch_project_asset", {"token": auth_user, "url": "http://127.0.0.1:9999/dummy"})
    data = json.loads(res.content[0].text)
    assert "error" in data # Because 9999 is closed, requests throws connection error, which is caught.

@pytest.mark.asyncio
async def test_summarize_task_legitimate(mcp_client, auth_user, two_teams):
    """22. Summarize task correctly templates prompt."""
    project_id = await _create_project(mcp_client, auth_user, two_teams["alpha"])
    task_id = await _create_task_in_project(mcp_client, auth_user, project_id, "Fix login")
    res = await mcp_client.call_tool("summarize_task", {
        "token": auth_user, "task_id": task_id, "custom_instruction": "Keep it short."
    })
    data = json.loads(res.content[0].text)
    assert data["prompt"] == "System: You are an AI assistant. Keep it short.\n\nPlease summarize this task: Fix login"

@pytest.mark.asyncio
async def test_load_custom_formatter_legitimate(mcp_client, auth_user):
    """23. Load safe python module."""
    res = await mcp_client.call_tool("load_custom_formatter", {"token": auth_user, "module_name": "json"})
    data = json.loads(res.content[0].text)
    assert data["status"] == "Loaded json"
    assert "doc" in data
