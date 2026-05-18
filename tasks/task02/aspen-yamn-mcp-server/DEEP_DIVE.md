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
| code_injection (1) | RUB-002 | Blocks import/exec expressions in `calculate_budget` |
| credentials_multi_caller (1) | RUB-003 | Denies diagnostic secrets to both unauthenticated and non-admin callers |
| untrusted_module_loading (1) | RUB-004 | Rejects path-style module names in `load_custom_formatter` |
| regression_legitimate_flows (1) | RUB-005 | Confirms same-team non-admin CRUD operations still work [RG] |
| ssrf_nonfetch (1) | RUB-006 | Blocks internal-IP fetch with content-level non-retrieval proof |
| safe_module_loading_controls (1) | RUB-007 | Rejects dangerous module chains while allowing safe built-ins |
| regression_same_team_lifecycle (1) | RUB-008 | Confirms task+comment end-to-end lifecycle for same-team non-admin [RG] |
| eval_result_field_clean (1) | RUB-009 | Injection expressions leave no execution markers; arithmetic returns correct value |
| fetch_asset_multi_variant (1) | RUB-010 | Multiple internal-address variants all rejected with content-level proof |
| legacy_diagnostic_multi_caller (1) | RUB-011 | Legacy secret-key markers absent for both unauthenticated and non-admin callers |
| ping_injection_multi_payload (1) | RUB-012 | Three+ injection payload shapes each blocked with full-body execution-artifact check |
| cross_team_search_isolation (1) | RUB-013 | Create→dual-search proves task visible to own team, absent from cross-team query |
| delete_verify_dual_surface (1) | RUB-014 | Delete→search-empty + update-not-found confirms deletion propagates across tool surfaces |

**Total: 14 items.** 9 critical (×4) + 5 major (×3) = 36 + 15 = **51 points max.**

## How to Read the Calibration Numbers

Once calibration is run (N=12 per model):

- **Mean Reward** — Average rubric score as fraction of max (38). Higher = model catches more vulnerabilities.
- **Saturation Rate** — Fraction of runs that score ≥ 80% of max. Measures consistency.
- **Pass Rate** — Fraction of runs where smoke tests (all 23 legitimate flows) still pass after adding the exfiltration suite.
- **Catch Rate per rubric** — How often each vulnerability is caught.

**Discrimination ladder:**
- **Floor** (both models pass — Type D): RUB-001, RUB-002, RUB-005 [RG], RUB-006, RUB-010
- **Hard floor** (both models fail — Type A): RUB-004, RUB-007
- **Core signal** (Opus passes, Qwen fails — Type B): RUB-003, RUB-008 [RG], RUB-009, RUB-011, RUB-012, RUB-013, RUB-014
