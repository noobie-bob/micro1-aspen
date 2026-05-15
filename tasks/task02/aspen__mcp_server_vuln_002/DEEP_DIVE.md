# Deep Dive: Vulnerable FastMCP ProjHub Server

## Five-Second Summary

This task presents a minimal but highly vulnerable **FastMCP (Model Context Protocol) server** managing a ProjHub-like domain (teams, projects, tasks, comments). The service contains **13 seeded security vulnerabilities** spread across 11 OWASP classes — from OS command injection and unsafe `eval()` execution to Server-Side Request Forgery (SSRF), prompt injection, missing access control, and credential exposure. The agent must author an extensive security test suite that catches every one of these vulnerabilities without over-blocking legitimate MCP tool usage.

## Why Test-Authoring Is the Right Shape

The **dual-contract argument**: a secure AI tool server (MCP) must enforce two invariants simultaneously:

1. **Isolation contract** — Users must not be able to abuse tools to exfiltrate internal system data, execute arbitrary OS commands, blind-fetch internal assets, or manipulate the LLM prompt. Tools meant for admins must remain protected.
2. **Usability contract** — Legitimate flows (such as searching tasks, calculating legitimate math expressions, or pinging safe targets) must continue working seamlessly after the bugs are patched.

A bug-fix task would let the agent patch one or two tools and call it done. A test-authoring task forces the agent to **induce the full threat model from the tools** — evaluating the inputs and outputs of every single registered MCP tool — and encode both the isolation and usability contracts as executable assertions.

## What the Agent Sees

The agent lands in `/repo` with:

```text
/repo/
├── mcp_server/                 # The FastMCP service (DO NOT MODIFY)
│   ├── server.py               # The MCP server with 17 tools (legit + vulnerable)
│   └── db.py                   # In-memory storage for ProjHub data
├── tests/
│   ├── conftest.py             # Fixtures: fastmcp.Client, auth tokens, test data
│   └── test_smoke.py           # 23 load-bearing legitimate-flow tests
├── requirements.txt
└── pytest.ini
```

The agent reads `prompt.txt` (which narrates a teammate's discovery of arbitrary command execution, internal data leaks, auth bypass, and prompt injection but does NOT list the rubric), then explores the `mcp_server/server.py` codebase to find all vulnerability surfaces.

### Auth Model (Passed as `token` arg)

| Token | Role | User ID | Team |
|-------|------|---------|------|
| `admin-key` | admin | admin-uuid | org-wide |
| `user-key` | user | alice-uuid | team-alpha (via fixture) |
| `user2-key` | user | bob-uuid | team-beta (via fixture) |
| `bypass-*` | user | bypass-uuid | **BUG**: Bypasses auth validation |

### Key Code Patterns to Notice

**OS Command Injection** — Unsanitized shell execution:
```python
# mcp_server/server.py
@mcp.tool()
def ping_team_server(token: str, target: str) -> str:
    # BUG: OS Command Injection via shell=True
    cmd = f"ping -n 1 {target}" if platform.system() == "Windows" else f"ping -c 1 {target}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
```

**Code Injection** — Unsafe Python eval:
```python
# mcp_server/server.py
@mcp.tool()
def calculate_budget(token: str, expression: str) -> str:
    # BUG: Code Injection
    result = eval(expression)
```

**Prompt Injection (Direct/Indirect)** — Blindly concatenating user/DB inputs into system prompts:
```python
# mcp_server/server.py
@mcp.tool()
def summarize_task(token: str, task_id: str, custom_instruction: str) -> str:
    # BUG: Prompt Injection
    prompt = f"System: You are an AI assistant. {custom_instruction}\n\nPlease summarize this task: {task['title']}"
```

**SSRF** — Unrestricted remote fetches:
```python
# mcp_server/server.py
@mcp.tool()
def fetch_project_asset(token: str, url: str) -> str:
    # BUG: SSRF
    resp = requests.get(url, timeout=5)
```

**Missing Function Level Access Control** — Admin tool lacking validation:
```python
# mcp_server/server.py
@mcp.tool()
def admin_sysinfo() -> str:
    # BUG: Missing auth check
    return json.dumps({"os": platform.system(), "status": "healthy"})
```

## How the Rubric Decomposes the Scenario

| Category | Items | What It Tests |
|----------|-------|---------------|
| command_injection (1) | RUB-001 | Blocks shell metacharacters in `ping_team_server` |
| code_injection (1) | RUB-002 | Blocks arbitrary Python code in `calculate_budget` |
| ssrf (1) | RUB-003 | Blocks internal IP fetching in `fetch_project_asset` |
| direct_prompt_injection (1) | RUB-004 | Sanitizes `custom_instruction` in `summarize_task` |
| indirect_prompt_injection (1) | RUB-005 | Sanitizes `task_title` in `summarize_task` |
| authentication (1) | RUB-006 | Rejects `bypass-` token prefixes |
| assets_management (1) | RUB-007 | Ensures `legacy_dump` tool is removed or inaccessible |
| credentials_exposure (1) | RUB-008 | Asserts `legacy_dump` doesn't leak hardcoded keys |
| sensitive_data_exposure (1) | RUB-009 | Asserts exceptions don't leak full python tracebacks |
| access_control (1) | RUB-010 | Ensures `admin_sysinfo` is protected by admin token |
| untrusted_components (1) | RUB-011 | Restricts arbitrary module imports in `load_custom_formatter` |
| regression_guard (2) | RUB-012–013 | Ensures legitimate math and pings continue working (Anti-overblock) |
| test_quality (1) | RUB-014 | Asserts tests use strict observability rather than just assuming exceptions mean success |

**Total: 14 items.** 11 major (×3) + 2 minor (×2) + 1 nitpick (×1) = **38 points max.**

## How to Read the Calibration Numbers

Once calibration is run (N=12 per model):

- **Mean Reward** — Average rubric score as fraction of max (38). Higher = model catches more vulnerabilities.
- **Saturation Rate** — Fraction of runs that score ≥ 80% of max. Measures consistency.
- **Pass Rate** — Fraction of runs where smoke tests (all 23 legitimate flows) still pass after adding the exfiltration suite.
- **Catch Rate per rubric** — How often each vulnerability is caught.

**Discrimination ladder:**
- **Floor** (any model catches): Command injection, SSRF, Access control (RUB-001, RUB-003, RUB-010)
- **Mid** (strong models catch): Prompt injection, Auth bypass, Code injection (RUB-004, RUB-005, RUB-006, RUB-002)
- **Ceiling** (frontier-only): Untrusted components, Traceback leaks (RUB-011, RUB-009)
- **Top-of-frontier**: Strict test quality, Regression guards (RUB-012, RUB-013, RUB-014)
