"""Helper utilities for FastMCP exfiltration tests."""

from __future__ import annotations

import json
from typing import Any


def result_to_text(result: Any) -> str:
    """Extract text payload from a FastMCP tool result."""
    if not getattr(result, "content", None):
        return ""
    first = result.content[0]
    return getattr(first, "text", str(first))


def payload_to_text(ok: bool, payload: Any) -> str:
    if ok:
        try:
            return json.dumps(payload, sort_keys=True)
        except TypeError:
            return str(payload)
    return str(payload)


async def call_tool_capture(mcp_client, tool: str, args: dict[str, Any] | None = None) -> tuple[bool, Any]:
    """Call a tool and capture either parsed JSON payload or exception text."""
    if args is None:
        args = {}

    try:
        result = await mcp_client.call_tool(tool, args)
    except Exception as exc:  # pragma: no cover - exception path is part of behavior checks.
        return False, str(exc)

    text = result_to_text(result)
    try:
        return True, json.loads(text)
    except json.JSONDecodeError:
        return True, {"raw": text}


async def create_project(mcp_client, token: str, team_id: str, name: str, description: str = "") -> str:
    ok, payload = await call_tool_capture(
        mcp_client,
        "create_project",
        {
            "token": token,
            "team_id": team_id,
            "name": name,
            "description": description,
        },
    )
    assert ok, f"create_project failed: {payload}"
    assert isinstance(payload, dict) and "id" in payload, f"unexpected project payload: {payload}"
    return payload["id"]


async def create_task(
    mcp_client,
    token: str,
    project_id: str,
    title: str,
    priority: str = "medium",
) -> str:
    ok, payload = await call_tool_capture(
        mcp_client,
        "create_task",
        {
            "token": token,
            "project_id": project_id,
            "title": title,
            "priority": priority,
        },
    )
    assert ok, f"create_task failed: {payload}"
    assert isinstance(payload, dict) and "id" in payload, f"unexpected task payload: {payload}"
    return payload["id"]
