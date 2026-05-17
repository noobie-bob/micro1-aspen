# aspen__test_authoring_projhub_visibility_001

## Tasks in this pack

| Substrate | Rubric Items | Max Score | Status |
|-----------|-------------|-----------|--------|
| projhub (Flask, ~1.5k LOC) | 18 (5 critical + 12 major + 1 minor) | 58 | Type B expansion added — recalibration pending |

## Substrate Summary

ProjHub is a Flask project-management API with teams, projects, tasks, comments, attachments, search, reports, admin surfaces, and unauthenticated diagnostics. The current rubric focuses on cross-boundary visibility failures, sensitive data exposure, search-query abuse, report command execution, and dual-contract regression guards.

## Current Rubric Shape

| Category | Items | Notes |
|----------|-------|-------|
| ownership | RUB-001, RUB-017, RUB-018 | destructive cross-boundary operations, secondary file channels, workflow mutation invariants |
| redaction | RUB-002 | admin-only field absence in non-privileged detail views |
| admin_endpoint | RUB-003, RUB-013 | audit and reporting surfaces denied to non-admin callers |
| sensitive_data_exposure | RUB-004, RUB-005, RUB-010, RUB-011, RUB-012 | credential and introspection diagnostics denied across caller classes |
| sql_injection | RUB-014, RUB-015 | crafted discovery-query visibility widening and restricted-marker extraction |
| command_injection | RUB-016 | shell-breakout denial with benign report-generation control |
| regression_guard | RUB-006, RUB-007, RUB-008, RUB-009 | admin visibility plus same-boundary read, write, and action-path usability |

Severity math: `5×4 + 12×3 + 1×2 = 58`.

## Latest Status

- The prior 13-item trimmed rubric could not reach the target range by trimming alone.
- Based on the latest supplied run set, the pre-expansion rubric sat at Opus `50.6%`, Qwen `47.5%`, spread `3.1%`.
- This update adds five intended Type B rungs: RUB-014 through RUB-018.
- Recalibration is required before any discrimination verdict can be claimed for the expanded rubric.

## Gold-Test Additions In This Revision

- Crafted search queries across both discovery surfaces must not widen cross-boundary visibility.
- Crafted task-search queries must not surface restricted indexed markers while benign search remains functional.
- Report generation must resist real shell-breakout payloads while a benign report request still works.
- Attachment list, direct download, and bundled download must preserve same-team access without leaking foreign filenames or bytes.
- Task assignment and transition endpoints must preserve same-team workflow changes while leaving foreign task state unchanged after denied attempts.

## Image

- **Tag:** `micro1ai/aspen-yamn-projecthub-flask:v1`
- **Digest:** `sha256:07c109d18f8a365af8caf779ce9f63c3b1796bd00282480cacdcf9025ea74d46`
- **Base commit:** `7d228305d9087ea8cb4784abd51784d687e44109`

## Calibration Results

Pending rerun after the Type B expansion. Do not treat any earlier 28-item or 13-item calibration notes as current for this task revision.
