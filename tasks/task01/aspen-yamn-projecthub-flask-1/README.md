# aspen__test_authoring_projhub_visibility_001

## Tasks in this pack

| Substrate | Rubric Items | Max Score | Status |
|-----------|-------------|-----------|--------|
| projhub (Flask, ~1.5k LOC) | 17 (3 critical + 13 major + 1 minor) | 53 | Safe trim applied, 3 intended Type B additions queued — recalibration pending |

## Substrate Summary

ProjHub is a Flask project-management API with teams, projects, tasks, comments, attachments, search, reports, admin surfaces, and unauthenticated diagnostics. The current rubric focuses on cross-boundary visibility failures, sensitive data exposure, search-query abuse, report command execution, and dual-contract regression guards.

## Current Rubric Shape

| Category | Items | Notes |
|----------|-------|-------|
| ownership | RUB-001 | destructive cross-boundary operations |
| redaction | RUB-002, RUB-015 | admin-only field absence in resource detail views and discussion-thread internal marker filtering |
| admin_endpoint | RUB-003, RUB-012 | audit and reporting surfaces denied to non-admin callers |
| sensitive_data_exposure | RUB-004, RUB-005, RUB-010, RUB-011 | credential and introspection diagnostics denied across caller classes |
| sql_injection | RUB-013, RUB-014 | crafted discovery-query visibility widening and restricted-marker extraction |
| improper_assets | RUB-016 | legacy identity-discovery surface must not permit privilege or existence enumeration |
| regression_guard | RUB-006, RUB-007, RUB-008, RUB-009, RUB-017 | admin visibility plus same-boundary read, write, action-path usability, and admin-positive-control diagnostics |

Severity math: `3×4 + 13×3 + 1×2 = 53`.

## Latest Status

- The prior 13-item trimmed rubric could not reach the target range by trimming alone.
- Based on the latest supplied run set, the pre-expansion rubric sat at Opus `50.6%`, Qwen `47.5%`, spread `3.1%`.
- The safe trim candidate removes former RUB-010, RUB-016, RUB-017, and RUB-018.
- This revision adds three intended Type B rungs at RUB-015 through RUB-017.
- Recalibration is required before any discrimination verdict can be claimed for the updated 17-item rubric.

## Intended Type B Additions In This Revision

- Discussion-thread filtering now has an intended positive-control rung: ordinary same-boundary comments stay visible while internal-only marker text remains absent.
- A legacy identity-discovery surface is now explicitly in scope for non-enumeration coverage.
- Operator-only diagnostics now have an intended admin-positive-control regression guard so fixes do not over-block admin access.

## Image

- **Tag:** `micro1ai/aspen-yamn-projecthub-flask:v1`
- **Digest:** `sha256:07c109d18f8a365af8caf779ce9f63c3b1796bd00282480cacdcf9025ea74d46`
- **Base commit:** `7d228305d9087ea8cb4784abd51784d687e44109`

## Calibration Results

Pending rerun after the safe trim plus three intended Type B additions. Do not treat earlier 18-item calibration notes as current for this task revision.
