# mcp_hub (FastMCP)

mcp_hub is a Python FastMCP server for teams, projects, tasks, comments, search, diagnostics, and utility tools. This repository contains a small, seeded substrate intended for writing focused exfiltration-style tests under `tests/exfiltration/`.

## Task metadata

- **Instance ID:** aspen__mcp_hub_fastmcp_001
- **Title:** Author simple Python tests for mcp_hub MCP security and product behavior
- **Repo source:** https://github.com/noobie-bob/micro1-aspen/tree/main/tasks/task06
- **Repo dir:** /mcp_hub
- **Image:** micro1ai/aspen-mcp_hub_fastmcp:security-v1
- **Image digest:** sha256:e94d420e2d41d247023d5bd3159052e174c1012111a19b9fbb4cbb1239f3222b
- **Base commit:** 484e1c60642be13c9315097114d673cec207ee5e

## Test surface

Tests can call tools directly through the substrate API or exercise helper call sites. Example:

```python
import app

app.reset_store()
result = app.call_tool("get_project", {
    "token": "user-key",
    "project_id": "project-alpha",
})
```

Always serialize responses (e.g., `.json()` or `json.dumps(...)`) before asserting on sentinel markers or internal fields.

## Run server

```bash
python app.py
```

## Substrate summary

This FastMCP substrate implements role-based behaviors and small utility tools. The seeded scenario focuses on visibility and information-shape concerns (what a caller can read back), not heavy stateful workflows. Legitimate product contracts (same-team access, admin access, delegated flows) must remain intact while exfiltration-style tests assert presence/absence of seeded markers.

## Vulnerability classes (CWEs)

This task targets information exposure and access control scenarios. CWEs listed in the task config:

- CWE-200, CWE-209, CWE-22, CWE-78, CWE-94, CWE-284, CWE-287, CWE-639, CWE-862, CWE-863, CWE-918

## Rubric (summary)

Tests submitted under `tests/exfiltration/` should address the ground-truth items below; they are used by the grader to score submissions. `rubric_max_score` = 31.

| ID | Severity | Category | Short description |
|----|----------|----------|-------------------|
| RUB-001 | critical | same_team_participant_access | user-key reads same-team seeded data |
| RUB-002 | major | tool_call_basic | call a valid tool and assert expected marker |
| RUB-003 | major | asset_fetch | asset fetch must not expose internal metadata |
| RUB-004 | major | diagnostic_non_leak | diagnostic surface must not leak seeded secret |
| RUB-005 | major | search_basic | same-team search returns expected alpha task |
| RUB-006 | major | admin_cross_team_access | admin-key can read cross-team data |
| RUB-007 | minor | repeatability | tests are independent and reproducible |
| RUB-008 | minor | serialized_assertions | serialize responses before checking markers |
| RUB-009 | nitpick | captured_values | use explicit expected values in assertions |
| RUB-010 | nitpick | serialization_helper_reuse | reuse a serialization helper across tests |
| RUB-011 | major | second_participant_same_team_access | user2-key reads beta same-team data |
| RUB-012 | major | cross_team_denial_serialized_marker_check | denied user cross-team access must not expose beta marker |

## Submission

- Place exfiltration tests in `tests/exfiltration/` so the expected diff path matches the task config.

## Notes

- Follow the behavioral prompt in `prompt.txt` (the prompt describes symptoms and legitimate flows; do not leak rubric details into smoke tests).
- Maintain independent tests (reset or reseed state) to satisfy repeatability requirements.

