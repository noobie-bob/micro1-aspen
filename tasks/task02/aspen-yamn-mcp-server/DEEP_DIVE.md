# Deep Dive: Vulnerable FastMCP ProjHub Server

## Five-Second Summary

This task presents a minimal **FastMCP (Model Context Protocol) server** managing a ProjHub-like domain (teams, projects, tasks, comments). The service exposes tools for project management, budget calculation, asset fetching, and system diagnostics. The agent must author an extensive security test suite that catches all security issues without over-blocking legitimate MCP tool usage.

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
│   ├── server.py               # The MCP server with tools for ProjHub domain
│   └── db.py                   # In-memory storage for ProjHub data
├── tests/
│   ├── conftest.py             # Fixtures: fastmcp.Client, auth tokens, test data
├── requirements.txt
└── pytest.ini
```

The agent reads `prompt.txt` (which mentions unexpected tool behaviour and access boundary concerns but does NOT list the rubric), then explores the `mcp_server/server.py` codebase to find all vulnerability surfaces.

### Auth Model (Passed as `token` arg)

| Token | Role | User ID | Team |
|-------|------|---------|------|
| `admin-key` | admin | admin-uuid | org-wide |
| `user-key` | user | alice-uuid | team-alpha (via fixture) |
| `user2-key` | user | bob-uuid | team-beta (via fixture) |

## How the Rubric Decomposes the Scenario

| Category | Items | What It Tests |
|----------|-------|---------------|
| command_injection (1) | RUB-001 | Blocks shell metacharacters in `ping_team_server` |
| code_injection (1) | RUB-002 | Blocks arbitrary Python code in `calculate_budget` |
| ssrf (1) | RUB-003 | Blocks internal IP fetching in `fetch_project_asset` |
| direct_prompt_injection (1) | RUB-004 | Sanitizes `custom_instruction` in `summarize_task` |
| indirect_prompt_injection (1) | RUB-005 | Sanitizes `task_title` in `summarize_task` |
| authentication (1) | RUB-006 | Rejects weak authentication bypass patterns |
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
