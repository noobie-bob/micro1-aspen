# aspen__projecthub_visibility_003

## Tasks in this pack

| Substrate | Stack | Rubric items | Max score | Status |
|-----------|-------|--------------:|----------:|--------|
| projecthub | Go `net/http` | 39 (8 critical, 20 major, 7 minor, 4 nitpick) | 110 | DRAFT |

## Calibration results

| Model | N | Mean Reward | Saturation Rate | Pass Rate | Distribution |
|-------|---:|------------:|----------------:|----------:|--------------|
| Claude Opus 4.7 | 12 | TBD | TBD | TBD | TBD |
| Qwen 3.5 | 4 | TBD | TBD | TBD | TBD |
| Gemini | 10 | TBD | TBD | TBD | TBD |

## gemini N=10 stability

Reward threshold >= 0.60

| k | pass@k |
|---:|:------|
| 1 | TBD |
| 5 | TBD |
| 10 | TBD |

Reward threshold >= 0.80

| k | pass@k |
|---:|:------|
| 1 | TBD |
| 5 | TBD |
| 10 | TBD |

## Per-rubric catch rates (N=12)

| Rubric | Severity | Category | Opus Catch | Qwen Catch |
|--------|----------|----------|-----------:|-----------:|
| RUB-001 | critical | access_control_chain | TBD | TBD |
| RUB-002 | critical | redaction_chain | TBD | TBD |
| RUB-003 | critical | stateful_share_chain | TBD | TBD |
| RUB-004 | critical | mass_assignment_chain | TBD | TBD |
| RUB-005 | critical | debug_legacy_ops_chain | TBD | TBD |
| RUB-006 | critical | injection_io_chain | TBD | TBD |
| RUB-007 | critical | weak_token_chain | TBD | TBD |
| RUB-008 | critical | error_exposure_chain | TBD | TBD |
| RUB-009 | major | mirror_child_scope | TBD | TBD |
| RUB-010 | major | archive_private_scope | TBD | TBD |
| RUB-011 | major | audit_scope | TBD | TBD |
| RUB-012 | major | report_scope | TBD | TBD |
| RUB-013 | major | comment_internal_consistency | TBD | TBD |
| RUB-014 | major | attachment_class_scope | TBD | TBD |
| RUB-015 | major | search_debug_flag | TBD | TBD |
| RUB-016 | major | legacy_auth | TBD | TBD |
| RUB-017 | major | ops_cursor_replay | TBD | TBD |
| RUB-018 | major | share_expiry_replay | TBD | TBD |
| RUB-019 | major | assignee_owner_mixup | TBD | TBD |
| RUB-020 | major | number_shadow_mixup | TBD | TBD |
| RUB-021 | major | admin_positive_detail | TBD | TBD |
| RUB-022 | major | lead_positive_detail | TBD | TBD |
| RUB-023 | major | participant_positive_flow | TBD | TBD |
| RUB-024 | major | auditor_boundaries | TBD | TBD |
| RUB-025 | major | bundle_side_effects | TBD | TBD |
| RUB-026 | major | mutation_readback | TBD | TBD |
| RUB-027 | major | body_shape | TBD | TBD |
| RUB-028 | major | table_variants | TBD | TBD |
| RUB-029 | minor | pagination_boundary | TBD | TBD |
| RUB-030 | minor | bad_json_boundary | TBD | TBD |
| RUB-031 | minor | case_encoding_boundary | TBD | TBD |
| RUB-032 | minor | token_length_boundary | TBD | TBD |
| RUB-033 | minor | same_team_negative_control | TBD | TBD |
| RUB-034 | minor | admin_negative_control | TBD | TBD |
| RUB-035 | minor | repeatability | TBD | TBD |
| RUB-036 | nitpick | sentinel_markers | TBD | TBD |
| RUB-037 | nitpick | helper_quality | TBD | TBD |
| RUB-038 | nitpick | merged_flow_quality | TBD | TBD |
| RUB-039 | nitpick | diagnostic_messages | TBD | TBD |

## Discrimination ladder rung breakdown

| Rung | Intended role | Current count | Notes |
|------|---------------|--------------:|-------|
| Floor | Broadly catchable baseline items | TBD | Fill after calibration |
| Mid-tier | Strong-model but not universal catches | TBD | Fill after calibration |
| Hard rungs | Frontier-skewed items | TBD | Fill after calibration |
| Top-of-frontier | Rare catches, ideally at least one item | TBD | Fill after calibration |

## Discrimination verdict

PENDING. The rubric is intentionally shaped as 8 merged critical chains plus supporting major, minor, and quality items, but the final verdict must wait for real calibration data. Mark it `DISCRIMINATIVE`, `UNDER-CALIBRATED`, or `FLAKY` only after the summary table, pass@k table, and per-rubric catch table are filled with observed results.

## Image

- Tag: `micro1ai/aspen-projecthub:visibility-v3`
- Digest: pending push or unavailable from current workspace context
- Base commit: image-derived commit hash; refresh after the next image rebuild if the build context changes

## Aspen pipeline gotchas

- The Docker image is the agent's working environment, not just a runtime artifact.
- There is no in-sandbox verifier, so `task_config.json` and the rubric descriptions must be self-consistent.
- `tests/smoke_test.go` is load-bearing and should ship in the image as the legitimate-flow reference.
- Prompt-level instruction-following matters: the prompt should describe symptoms, not enumerate the audit plan or rubric.
- The benchmark gets most of its difficulty from merged scenario chains, response-body assertions, and anti-overblock checks rather than raw endpoint count.
