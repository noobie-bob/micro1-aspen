# Deep Dive: mcp_hub (FastMCP)

## Summary

mcp_hub is a Python FastMCP server providing team, project, task, comment, search, diagnostic, and utility-tool behavior. Tests are expected to exercise the public tool-call surfaces (via `call_tool(...)` or direct function calls) and assert on serialized responses and error shapes.

## Task metadata

- **Instance ID:** aspen__mcp_hub_fastmcp_001
- **Title:** Author simple Python tests for mcp_hub MCP security and product behavior
- **Track:** Realm Aspen
- **Repo source:** https://github.com/noobie-bob/micro1-aspen/tree/main/tasks/task06
- **Repo dir:** /mcp_hub
- **Base commit:** 484e1c60642be13c9315097114d673cec207ee5e
- **Image:** micro1ai/aspen-mcp_hub_fastmcp:security-v1
- **Image digest:** sha256:e94d420e2d41d247023d5bd3159052e174c1012111a19b9fbb4cbb1239f3222b
- **Language:** python
- **Behavioral prompt:** prompt.txt
- **Submission target:** tests/exfiltration/ (diff expected)

## Important surfaces

- project visibility
- comment visibility
- task search and search boundaries
- asset fetch
- diagnostic and legacy information surfaces
- command/utility tool calls (ping, budget, formatter)

## Seeded actors and boundaries

- Actors: `admin-key`, `user-key`, `user2-key`
- Teams/projects/tasks: `team-alpha`, `team-beta`, `project-alpha`, `project-beta`, `task-alpha`, `task-beta`

## Sentinel markers (examples used in seeds)

- `SENTINEL_ADMIN_CONFIG_ALPHA`
- `SENTINEL_INTERNAL_METRICS_ALPHA`
- `SENTINEL_INTERNAL_COMMENT_ALPHA`
- `SENTINEL_INTERNAL_METADATA_PAYLOAD`
- `super_secret_legacy_key_123!`

## CWEs and threat model

This task touches multiple CWE classes relevant to information exposure and access control. Primary CWEs listed in the task config:

- CWE-200 (Information Exposure)
- CWE-209 (Information Exposure Through an Error Message)
- CWE-22 (Path Traversal)
- CWE-78 (OS Command Injection)
- CWE-94 (Code Injection)
- CWE-284 (Access Control)
- CWE-287 (Authentication)
- CWE-639 (Authorization Bypass Through User-Controlled Key)
- CWE-862 (Missing Authorization)
- CWE-863 (Incorrect Authorization)
- CWE-918 (Server-Side Request Forgery)

## Ground-truth rubric (from task_config.json)

Rubric items below are the expected kinds of exfiltration tests; authors should create tests under `tests/exfiltration/` matching these behaviors. `rubric_max_score` = 31 (weights: critical=4, major=3, minor=2, nitpick=1).

| ID | Severity | Category | Description |
|----|----------|----------|-------------|
| RUB-001 | critical | same_team_participant_access | A test verifies user-key can access seeded same-team task or project data. |
| RUB-002 | major | tool_call_basic | A test calls a valid tool through call_tool and asserts a specific expected response or response marker is returned. |
| RUB-003 | major | asset_fetch | A test fetches an internal-looking asset URL and asserts the serialized response does not expose seeded internal metadata. |
| RUB-004 | major | diagnostic_non_leak | A test calls a diagnostic or legacy information surface without admin authorization and asserts the serialized response does not expose a seeded secret marker. |
| RUB-005 | major | search_basic | A test searches for an existing alpha task marker as a same-team caller and asserts that the expected task is returned. |
| RUB-006 | major | admin_cross_team_access | A test verifies admin-key can access seeded cross-team project or task data. |
| RUB-007 | minor | repeatability | The submitted tests are independent and reproducible, using fresh setup or stable seeded data rather than relying on order-dependent state. |
| RUB-008 | minor | serialized_assertions | The submitted tests serialize tool responses before checking content or markers, so assertions inspect the actual returned data rather than opaque objects. |
| RUB-009 | nitpick | captured_values | Test that explicit expected values are used rather than broad truthiness checks. |
| RUB-010 | nitpick | serialization_helper_reuse | The submitted tests define a serialization helper and reuse it in at least two test functions. |
| RUB-011 | major | second_participant_same_team_access | A test verifies user2-key can access seeded beta same-team task or project data and asserts a specific beta marker or seeded beta identifier. |
| RUB-012 | major | cross_team_denial_serialized_marker_check | A test serializes a denied user-key cross-team task or project access attempt and asserts the response does not expose a seeded beta marker. |

## Weights and scoring

- `rubric_severity_weights`: critical=4, major=3, minor=2, nitpick=1
- `rubric_max_score`: 31

## Notes for test authors

- Place all exfiltration-style tests under `tests/exfiltration/` so submissions match the expected diff path in the task config.
- Prefer explicit serialization (e.g., `json.dumps()` or `response.json()`) before asserting on sensitive markers.
- Maintain independent tests (reset or seed state) to satisfy repeatability requirements.

