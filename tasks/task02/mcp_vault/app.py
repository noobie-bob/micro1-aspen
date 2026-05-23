from __future__ import annotations
from typing import Any
from mcp.server.fastmcp import FastMCP
import tools
from seed import new_store

mcp = FastMCP("mcp_vault", json_response=True)
STORE = new_store()

TOOL_REGISTRY = {
    "get_folder": tools.get_folder,
    "get_document": tools.get_document,
    "create_document": tools.create_document,
    "preview_document": tools.preview_document,
    "search_documents": tools.search_documents,
    "export_document": tools.export_document,
    "list_audit_records": tools.list_audit_records,
    "fetch_remote_attachment": tools.fetch_remote_attachment,
    "redact_text": tools.redact_text,
    "calculate_storage_cost": tools.calculate_storage_cost,
    "admin_diagnostics": tools.admin_diagnostics,
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
def get_folder(token: str, folder_id: str) -> dict[str, Any]:
    return call_tool("get_folder", locals())

@mcp.tool()
def get_document(token: str, document_id: str) -> dict[str, Any]:
    return call_tool("get_document", locals())

@mcp.tool()
def create_document(token: str, folder_id: str, title: str, body: str = "") -> dict[str, Any]:
    return call_tool("create_document", locals())

@mcp.tool()
def preview_document(token: str, document_id: str) -> dict[str, str]:
    return call_tool("preview_document", locals())

@mcp.tool()
def search_documents(token: str, q: str = "") -> list[dict[str, Any]]:
    return call_tool("search_documents", locals())

@mcp.tool()
def export_document(token: str, document_id: str, format: str = "json") -> dict[str, str]:
    return call_tool("export_document", locals())

@mcp.tool()
def list_audit_records(token: str, document_id: str) -> list[dict[str, Any]]:
    return call_tool("list_audit_records", locals())

@mcp.tool()
def fetch_remote_attachment(token: str, url: str) -> dict[str, str]:
    return call_tool("fetch_remote_attachment", locals())

@mcp.tool()
def redact_text(token: str, text: str) -> dict[str, str]:
    return call_tool("redact_text", locals())

@mcp.tool()
def calculate_storage_cost(token: str, expression: str) -> dict[str, Any]:
    return call_tool("calculate_storage_cost", locals())

@mcp.tool()
def admin_diagnostics(token: str | None = None) -> dict[str, str]:
    return call_tool("admin_diagnostics", locals())

if __name__ == "__main__":
    mcp.run()
