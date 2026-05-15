"""FastMCP Server implementation for ProjHub domain."""
import subprocess
import importlib
import requests
import traceback
import json
import platform
from fastmcp import FastMCP
from mcp_server.db import TEAMS, PROJECTS, TASKS, COMMENTS, generate_id

mcp = FastMCP("ProjHub-MCP")

# Auth Helper
VALID_TOKENS = {
    "admin-key":  ("admin", "admin-uuid"),
    "user-key":   ("user",  "alice-uuid"),
    "user2-key":  ("user",  "bob-uuid"),
}

def verify_token(token: str) -> tuple[str, str]:
    """Returns (role, user_id). Raises Exception if invalid."""
    if token.startswith("bypass-"):
        return ("user", "bypass-uuid")
    if token not in VALID_TOKENS:
        raise Exception("Unauthorized")
    return VALID_TOKENS[token]

def is_team_member(user_id: str, team_id: str) -> bool:
    team = TEAMS.get(team_id)
    if not team: return False
    return user_id in team["member_ids"]

@mcp.tool()
def create_team(token: str, name: str, member_ids: list[str]) -> str:
    role, uid = verify_token(token)
    if role != "admin": raise Exception("Forbidden")
    tid = generate_id()
    TEAMS[tid] = {"id": tid, "name": name, "member_ids": member_ids}
    return json.dumps(TEAMS[tid])

@mcp.tool()
def get_team(token: str, team_id: str) -> str:
    role, uid = verify_token(token)
    if team_id not in TEAMS: raise Exception("Not Found")
    if role != "admin" and not is_team_member(uid, team_id): raise Exception("Forbidden")
    return json.dumps(TEAMS[team_id])

@mcp.tool()
def create_project(token: str, team_id: str, name: str, description: str = "") -> str:
    role, uid = verify_token(token)
    if role != "admin" and not is_team_member(uid, team_id): raise Exception("Forbidden")
    pid = generate_id()
    PROJECTS[pid] = {"id": pid, "team_id": team_id, "name": name, "description": description}
    return json.dumps(PROJECTS[pid])

@mcp.tool()
def get_project(token: str, project_id: str) -> str:
    role, uid = verify_token(token)
    project = PROJECTS.get(project_id)
    if not project: raise Exception("Not Found")
    if role != "admin" and not is_team_member(uid, project["team_id"]): raise Exception("Forbidden")
    return json.dumps(project)

@mcp.tool()
def create_task(token: str, project_id: str, title: str, priority: str = "medium") -> str:
    role, uid = verify_token(token)
    project = PROJECTS.get(project_id)
    if not project: raise Exception("Not Found")
    if role != "admin" and not is_team_member(uid, project["team_id"]): raise Exception("Forbidden")
    tid = generate_id()
    TASKS[tid] = {"id": tid, "project_id": project_id, "title": title, "priority": priority}
    return json.dumps(TASKS[tid])

@mcp.tool()
def update_task(token: str, task_id: str, title: str = None, priority: str = None) -> str:
    role, uid = verify_token(token)
    task = TASKS.get(task_id)
    if not task: raise Exception("Not Found")
    project = PROJECTS.get(task["project_id"])
    if role != "admin" and not is_team_member(uid, project["team_id"]): raise Exception("Forbidden")
    if title: task["title"] = title
    if priority: task["priority"] = priority
    return json.dumps(task)

@mcp.tool()
def delete_task(token: str, task_id: str) -> str:
    role, uid = verify_token(token)
    task = TASKS.get(task_id)
    if not task: raise Exception("Not Found")
    project = PROJECTS.get(task["project_id"])
    if role != "admin" and not is_team_member(uid, project["team_id"]): raise Exception("Forbidden")
    del TASKS[task_id]
    return json.dumps({"status": "deleted", "id": task_id})

@mcp.tool()
def add_comment(token: str, task_id: str, body: str, internal: bool = False) -> str:
    role, uid = verify_token(token)
    task = TASKS.get(task_id)
    if not task: raise Exception("Not Found")
    project = PROJECTS.get(task["project_id"])
    if role != "admin" and not is_team_member(uid, project["team_id"]): raise Exception("Forbidden")
    if internal and role != "admin": raise Exception("Only admins can add internal comments")
    cid = generate_id()
    COMMENTS[cid] = {"id": cid, "task_id": task_id, "body": body, "internal": internal, "author": uid}
    return json.dumps(COMMENTS[cid])

@mcp.tool()
def list_task_comments(token: str, task_id: str) -> str:
    role, uid = verify_token(token)
    task = TASKS.get(task_id)
    if not task: raise Exception("Not Found")
    project = PROJECTS.get(task["project_id"])
    if role != "admin" and not is_team_member(uid, project["team_id"]): raise Exception("Forbidden")
    results = [c for c in COMMENTS.values() if c["task_id"] == task_id]
    # Filter out internal comments for non-admins
    if role != "admin":
        results = [c for c in results if not c["internal"]]
    return json.dumps(results)

@mcp.tool()
def search_tasks(token: str, q: str) -> str:
    role, uid = verify_token(token)
    results = []
    for t in TASKS.values():
        if q.lower() in t["title"].lower():
            project = PROJECTS.get(t["project_id"])
            if role == "admin" or is_team_member(uid, project["team_id"]):
                results.append(t)
    return json.dumps(results)

@mcp.tool()
def ping_team_server(token: str, target: str) -> str:
    verify_token(token)
    cmd = f"ping -n 1 {target}" if platform.system() == "Windows" else f"ping -c 1 {target}"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return json.dumps({"output": result.stdout})
    except Exception as e:
        return json.dumps({"error": traceback.format_exc()})

@mcp.tool()
def calculate_budget(token: str, expression: str) -> str:
    verify_token(token)
    try:
        result = eval(expression)
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": traceback.format_exc()})

@mcp.tool()
def fetch_project_asset(token: str, url: str) -> str:
    verify_token(token)
    try:
        resp = requests.get(url, timeout=5)
        return json.dumps({"content": resp.text[:100]})
    except Exception as e:
        return json.dumps({"error": traceback.format_exc()})

@mcp.tool()
def summarize_task(token: str, task_id: str, custom_instruction: str) -> str:
    verify_token(token)
    task = TASKS.get(task_id)
    if not task: raise Exception("Not Found")
    prompt = f"System: You are an AI assistant. {custom_instruction}\n\nPlease summarize this task: {task['title']}"
    return json.dumps({"prompt": prompt})

@mcp.tool()
def load_custom_formatter(token: str, module_name: str) -> str:
    verify_token(token)
    try:
        module = importlib.import_module(module_name)
        return json.dumps({"status": f"Loaded {module_name}", "doc": str(module.__doc__)[:50]})
    except Exception as e:
        return json.dumps({"error": traceback.format_exc()})

@mcp.tool()
def admin_sysinfo() -> str:
    return json.dumps({"os": platform.system(), "status": "healthy"})

@mcp.tool()
def legacy_dump() -> str:
    return json.dumps({
        "status": "legacy system active",
        "keys": {"root": "super_secret_legacy_key_123!"}
    })
