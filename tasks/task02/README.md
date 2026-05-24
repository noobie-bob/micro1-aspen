# aspen_mcpvault_security_002

Reference sample task for the Aspen evaluation pipeline — LLM-judge
**test authoring** for `mcp_vault` tool surfaces and seeded markers.

This task is `rubric_only`: agents author a hidden pytest suite that
captures seeded information-exposure and access-control regression
shapes. The judge scores the agent's git diff against `ground_truth_issues[]`.

## Tasks in this pack

| Task | Substrate | Rubric items | Status |
| --- | --- | ---: | --- |
| `aspen_mcpvault_security_002` | `mcp_vault` (Python FastMCP toolset) | 11 (1 critical + 7 major + 2 minor + 1 nitpick) | **PENDING-CALIBRATION** |

## Calibration results — `aspen_mcpvault_security_002`

Calibration data is not currently available in this repository. The
README scaffolds the expected sections (per-model summary, pass@k,
per-rubric catch rates, discrimination ladder). These sections will be
filled when fresh evaluation results are provided.

## Ground-truth rubric — `aspen_mcpvault_security_002`

| ID | Severity | Category | Criterion |
| --- | --- | --- | --- |
| RUB-001 | critical | same_org_get_document_alpha_id | Participant `get_document` for `doc-alpha` returns expected id |
| RUB-002 | major | valid_tool_call_specific_marker | Tool-call returns seeded alpha document marker |
| RUB-003 | major | same_org_search_alpha_result | `search_documents` query returns `doc-alpha` |
| RUB-004 | major | admin_get_document_beta_id | Admin `get_document` returns `doc-beta` |
| RUB-005 | major | admin_discovery_beta_private_note_present | Admin discovery includes seeded beta private-note |
| RUB-006 | minor | serialized_assertions | Tests serialize responses before asserting content |
| RUB-007 | minor | explicit_serialized_marker_assertion | Tests assert exact seeded beta private-note in serialized output |
| RUB-008 | nitpick | serialization_helper_reuse | Tests reuse a shared serialization helper |
| RUB-009 | major | participant_discovery_beta_private_note_non_leak | Participant discovery does not expose beta private-note |
| RUB-011 | major | cross_org_preview_denial | Cross-org preview attempts are denied to participants |
| RUB-012 | major | cross_org_document_fetch_denial | Cross-org document fetch attempts are denied to participants |

## Per-task contents

```
.
  README.md            # this file — team status report
  DEEP_DIVE.md         # outsider on-ramp: what is being graded, why it works
  prompt.txt           # 3-paragraph engineer-to-engineer ask (in metadata)
  task_config.json     # ground_truth_issues[], image, pipeline=aspen, rubric_only=true (in metadata)
  reasoning.txt        # task design rationale
  mcp_vault/           # substrate source (tool implementations, seed data)
  tests/               # smoke + gold-standard exfiltration tests (authoring target)
```

## Image

`micro1ai/aspen-mcp_vault_fastmcp:security-v1` (digest in
`aspen_mcpvault_security_002/task_config.json`)

## Aspen pipeline gotchas

- This task is `rubric_only`: scoring is rubric-judged, not deterministic
  in-sandbox verification.
- The `tests/test_smoke.py` and `mcp_vault/seed.py` are load-bearing and
  encode legitimate participant/admin role mappings (see `mcp_vault/common.py`).
- If calibration numbers are not supplied, README sections remain pending.
