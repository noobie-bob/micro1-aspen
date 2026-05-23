# aspen__mcp_go_projhub

Author simple Go unit tests for ProjHub MCP security and product-regression behavior.

## Tasks in this pack

| Substrate | Stack | Rubric items | Max score | Status |
|-----------|-------|--------------:|----------:|--------|
| projhubmcp | Go `net/http` | 12 (2 critical, 6 major, 3 minor, 1 nitpick) | 33 | Calibration pending |

## Substrate summary

ProjHub MCP is a compact Go service that exposes a small MCP-style HTTP surface (`/mcp` + tool endpoints) for teams, projects, tasks, and comments. The seeded scenario is a cross-team visibility leak that manifests across multiple retrieval and summarization paths (project reads, task summaries, search, comment lists and exported assets) rather than a single endpoint bug. The agent's deliverable is a Go test suite placed under `tests/exfiltration/` that both (1) catches the seeded leaks and (2) detects over-eager fixes that would break legitimate same-team and admin flows.

## Image

- **Tag:** `micro1ai/aspen-mcp-go:security-v3`
- **Digest:** `sha256:563f22421cc0ff66c1dc68580c881bba375e3a36cfb8ebb8cddb750cfdd1dc6d`
- **Base commit:** `dd0b7a2da480d59f79c5e98484c54e1049164400`

## Submission

- **Expected submission path:** `tests/exfiltration/` (see `prompt.txt`)
- **Presentation:** `git_diff` of the new test files

## Rubric (from task_config.json)

| Rubric | Severity | Category |
|--------|----------|----------|
| RUB-001 | critical | same_team_participant_access |
| RUB-002 | major | admin_project_visibility |
| RUB-003 | minor | repeatability |
| RUB-004 | minor | serialized_assertions |
| RUB-005 | major | cross_team_search_non_leak |
| RUB-006 | nitpick | serialization_helper_reuse |
| RUB-007 | major | second_participant_same_team_access |
| RUB-008 | minor | cross_team_denial_serialized_marker_check |
| RUB-009 | critical | cross_team_project_config_non_leak |
| RUB-010 | major | cross_team_summary_title_non_leak |
| RUB-011 | major | internal_comment_marker_hidden |
| RUB-012 | major | cross_team_summary_non_leak |

**Rubric weights:** critical=4, major=3, minor=2, nitpick=1 → max score = 33

## Per-task contents

```
.  README.md            # this file — team status report
	DEEP_DIVE.md         # outsider on-ramp: what is being graded, why it works
	prompt.txt           # 3-paragraph engineer-to-engineer ask
	task_config.json     # ground_truth_issues[], image, pipeline=aspen, rubric_only=true
	reasoning.txt        # (optional) task design rationale
	projhubmcp/          # Go substrate (common.go, tools.go, seed.go, types.go, wire.go)
	tests/               # smoke and expected exfiltration tests
	tests/smoke_test.go  # legitimate-flow smoke test
	tests/exfiltration/  # expected submission folder
```

## Aspen pipeline notes

- The Docker image is the agent's working environment. `task_config.json` is authoritative about `repo.image_name` and `repo.base_commit`.
- This task is `rubric_only: true`: there is no in-sandbox verifier. The judge converts each `ground_truth_issues[]` entry into one NL assertion graded by severity.
- The prompt (`prompt.txt`) instructs the agent to write tests only and to place them under `tests/exfiltration/` — do not modify server code.
- The `tests/smoke_test.go` encodes the legitimate participant/admin flows; keep those flows working in your test-suite framing (anti-overblock guards).
