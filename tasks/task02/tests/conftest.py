"""Shared test fixtures for mcp_server."""
import pytest
import pytest_asyncio
from fastmcp import Client
import json
from mcp_server.server import mcp
from mcp_server.db import reset_state, TEAMS

@pytest_asyncio.fixture()
async def mcp_client():
    reset_state()
    async with Client(mcp) as client:
        yield client

@pytest.fixture()
def auth_admin():
    return "admin-key"

@pytest.fixture()
def auth_user():
    return "user-key"

@pytest.fixture()
def auth_user2():
    return "user2-key"

@pytest_asyncio.fixture()
async def two_teams(mcp_client, auth_admin):
    """Create two teams and assign alice to team-alpha, bob to team-beta."""
    alpha_result = await mcp_client.call_tool("create_team", {
        "token": auth_admin,
        "name": "team-alpha",
        "member_ids": ["alice-uuid"]
    })
    alpha_id = json.loads(alpha_result.content[0].text)["id"]

    beta_result = await mcp_client.call_tool("create_team", {
        "token": auth_admin,
        "name": "team-beta",
        "member_ids": ["bob-uuid"]
    })
    beta_id = json.loads(beta_result.content[0].text)["id"]

    return {"alpha": alpha_id, "beta": beta_id}
