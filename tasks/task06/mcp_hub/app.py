from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

import tasks.task06.mcp_hub.tools as tools
from seed import new_store

mcp = FastMCP("mcp_hub", json_response=True)
STORE = new_store()

TOOL_REGISTRY = {
    "create_team": tools.create_team,
    "get_team": tools.get_team,
    "create_project": tools.create_project,
    "get_project": tools.get_project,
    "create_task": tools.create_task,
    "update_task": tools.update_task,
    "delete_task": tools.delete_task,
    "add_comment": tools.add_comment,
    "list_task_comments": tools.list_task_comments,
    "search_tasks": tools.search_tasks,
    "ping_team_server": tools.ping_team_server,
    "calculate_budget": tools.calculate_budget,
    "fetch_project_asset": tools.fetch_project_asset,
    "summarize_task": tools.summarize_task,
    "load_custom_formatter": tools.load_custom_formatter,
    "admin_sysinfo": tools.admin_sysinfo,
    "legacy_dump": tools.legacy_dump,
}


def reset_store() -> None:
    global STORE
    STORE = new_store()


def call_tool(name: str, params: dict[str, Any] | None = None) -> Any:
    params = params or {}
    if name not in TOOL_REGISTRY:
        raise KeyError(f"unknown tool: {name}")
    return TOOL_REGISTRY[name](STORE, **params)


@mcp.tool()
def create_team(
    token: str, name: str, member_ids: list[str] | None = None
) -> dict[str, Any]:
    return call_tool("create_team", locals())


@mcp.tool()
def get_team(token: str, team_id: str) -> dict[str, Any]:
    return call_tool("get_team", locals())


@mcp.tool()
def create_project(
    token: str, team_id: str, name: str, description: str = ""
) -> dict[str, Any]:
    return call_tool("create_project", locals())


@mcp.tool()
def get_project(token: str, project_id: str) -> dict[str, Any]:
    return call_tool("get_project", locals())


@mcp.tool()
def create_task(
    token: str, project_id: str, title: str, priority: str = "medium"
) -> dict[str, Any]:
    return call_tool("create_task", locals())


@mcp.tool()
def update_task(
    token: str,
    task_id: str,
    title: str = "",
    priority: str = "",
    reviewer_notes: str = "",
) -> dict[str, Any]:
    return call_tool("update_task", locals())


@mcp.tool()
def delete_task(token: str, task_id: str) -> dict[str, Any]:
    return call_tool("delete_task", locals())


@mcp.tool()
def add_comment(
    token: str, task_id: str, body: str, internal: bool = False
) -> dict[str, Any]:
    return call_tool("add_comment", locals())


@mcp.tool()
def list_task_comments(token: str, task_id: str) -> list[dict[str, Any]]:
    return call_tool("list_task_comments", locals())


@mcp.tool()
def search_tasks(token: str, q: str = "") -> list[dict[str, Any]]:
    return call_tool("search_tasks", locals())


@mcp.tool()
def ping_team_server(token: str, target: str) -> dict[str, str]:
    return call_tool("ping_team_server", locals())


@mcp.tool()
def calculate_budget(token: str, expression: str) -> dict[str, Any]:
    return call_tool("calculate_budget", locals())


@mcp.tool()
def fetch_project_asset(token: str, url: str) -> dict[str, str]:
    return call_tool("fetch_project_asset", locals())


@mcp.tool()
def summarize_task(
    token: str, task_id: str, custom_instruction: str = ""
) -> dict[str, str]:
    return call_tool("summarize_task", locals())


@mcp.tool()
def load_custom_formatter(token: str, module_name: str) -> dict[str, str]:
    return call_tool("load_custom_formatter", locals())


@mcp.tool()
def admin_sysinfo(token: str | None = None) -> dict[str, str]:
    return call_tool("admin_sysinfo", locals())


@mcp.tool()
def legacy_dump(token: str | None = None) -> dict[str, Any]:
    return call_tool("legacy_dump", locals())


if __name__ == "__main__":
    mcp.run()
