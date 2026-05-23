
# Deep Dive — aspen__mcp_go_projhub

> **Audience.** Reader unfamiliar with this repo or task. This file explains what an AI model is being graded on, what the seeded leak looks like in code, why the substrate is realistic, and what to watch for when reading calibration results.

---

## 1. Five-second summary

Ask: write a Go test suite that catches cross-team visibility leaks in a compact MCP-style Go service. The agent must (a) detect the seeded leak surfaces and (b) write anti-overblock tests that prove legitimate same-team and admin flows remain functional.

## 2. Why test-authoring is the right shape

Fix shapes for visibility problems vary (redact, gate, or storage-layer fixes). Asking the agent to write tests isolates *threat-model induction* from implementation taste: a good suite catches the leak across retrieval and write-side laundering surfaces while also asserting the dual contract (leak closed, legitimate flows preserved).

## 3. What the agent sees

- Small Go module mounted at `/repo`.
- Key files: `projhubmcp/wire.go` (HTTP → MCP method dispatch), `projhubmcp/tools.go` (token verification: `admin-key`, `user-key`, `user2-key`), `projhubmcp/common.go` (helpers, response writers, side-effect helpers), `projhubmcp/seed.go` (seeded teams/projects/tasks/comments with sentinel markers), `projhubmcp/types.go` (data shapes), and `tests/smoke_test.go` (legitimate-flow smoke test).
- Seeded data includes `project-alpha` (Name: "Apollo"), `project-beta` (Name: "Borealis"), `task-beta` title includes "Migrate DB", and internal comment markers such as `SENTINEL_INTERNAL_COMMENT_ALPHA`. Those sentinel values are the canonical markers used by the ground-truth rubric.

The MCP dispatch surface provides methods the agent will call in tests: `get_project`, `list_task_comments`, `search_tasks`, `summarize_task`, `fetch_project_asset`, `ping_team_server`, and various create/update/delete flows. Many of these return full structs (e.g., `Project`) or injected strings (e.g., `summarize_task` returns a prompt containing the task title), which is why response-shape and summary endpoints are grading surfaces.

## 4. Scenario shape in code

Two structural patterns produce the leak surface here:

- Centralised auth + `projectAllowed()` gating: most reads call a small set of helpers that decide reachability (Admin OR team member).
- Inconsistent projector/serializer choices: the same `Project` or `Task` objects are returned by many different helpers (direct reads, search results, summaries, exports). Some paths include admin-only fields (`AdminConfig`, `InternalMetrics`) or aggregate titles that carry seeded task names.

Those two axes lead to multi-surface leakage without any single-line bug; the seeded leak is observable from the outside via the public MCP endpoints.

## 5. How the rubric decomposes the scenario

The rubric maps directly to observable, external test behaviors. High-level grouping:

- **Critical (2):** same-team participant access test (RUB-001) and cross-team project-config non-leak (RUB-009). These must fail if privileged project fields or configs are recoverable by an ordinary participant.
- **Major (6):** admin visibility checks, cross-team search non-leak, second-participant same-team access, cross-team summary title non-leak, internal comment marker hidden, cross-team summary non-leak — these cover the majority of retrieval and anti-overblock guard behaviors.
- **Minor (3):** repeatability, serialized assertions (tests should assert on serialized outputs), and denial / marker checks for cross-team reads.
- **Nitpick (1):** reuse of a serialization helper across tests (DRY + sentinel assertion quality).

The `prompt.txt` explicitly asks tests to be placed under `tests/exfiltration/` and to avoid modifying server code. The judge will compare the submitted diff to the rubric entries in `task_config.json`.

## 6. What to look for when writing tests

- Prefer serialized assertions (marshal or inspect returned JSON) rather than asserting on opaque Go values.
- Seed-specific sentinels are the authenticity signal: `Apollo`, `Borealis`, `Migrate DB`, `SENTINEL_INTERNAL_COMMENT_ALPHA`, and `SENTINEL_*` metadata keys.
- Include anti-overblock assertions: add checks that admin and same-team happy-paths still succeed after the leak is closed.

## 7. Per-task contents

```
.  README.md
	DEEP_DIVE.md
	prompt.txt
	task_config.json
	reasoning.txt (optional)
	projhubmcp/          # Go substrate (common.go, tools.go, seed.go, types.go, wire.go)
	tests/               # smoke and exfiltration tests
	tests/smoke_test.go
	tests/exfiltration/  # expected submission folder
```

## 8. Aspen pipeline gotchas

- `rubric_only: true` — there is no in-sandbox verifier and no deterministic gold patch. The judge auto-generates NL assertions from `ground_truth_issues[]`.
- `task_config.repo.image_name` is the agent's working environment. Make sure any local reasoning assumes the agent runs in the image specified by `task_config.json`.
- The `tests/smoke_test.go` file is load-bearing: it documents legitimate flows and helps the agent understand which calls are participant-callable vs admin-only.



