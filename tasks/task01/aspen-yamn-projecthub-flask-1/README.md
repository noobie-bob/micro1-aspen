# aspen__test_authoring_projhub_visibility_001

## Tasks in this pack

| Substrate | Rubric Items | Max Score | Status |
|-----------|-------------|-----------|--------|
| projhub (Flask, ~1.5k LOC) | 19 (18 major + 1 minor) | 56 | Safe trim applied, 5 intended Type B additions queued — recalibration pending |

## Substrate Summary

ProjHub is a Flask project-management API with teams, projects, tasks, comments, attachments, search, reports, admin surfaces, and unauthenticated diagnostics. The current rubric focuses on cross-boundary visibility failures, sensitive data exposure, search-query abuse, report command execution, and dual-contract regression guards.

## Current Rubric Shape

| Category | Items | Notes |
|----------|-------|-------|
| ownership | RUB-001 | destructive cross-boundary operation denial with read-back invariants |
| redaction | RUB-002, RUB-011 | privileged field suppression in detail and derived views plus internal-comment filtering with a positive control |
| admin_endpoint | RUB-003, RUB-010 | operator activity and management surfaces denied to lower-privilege callers with an admin positive control |
| sensitive_data_exposure | RUB-004, RUB-009, RUB-015, RUB-017, RUB-018, RUB-019 | credential and runtime-diagnostic surfaces denied across caller classes with body-level non-leak assertions |
| regression_guard | RUB-005, RUB-006, RUB-007, RUB-008, RUB-012, RUB-013, RUB-014, RUB-016 | admin visibility plus same-boundary read, write, action-path usability, and admin-positive-control diagnostics |

Severity math: `18×3 + 1×2 = 56`.

## Latest Status

- The prior 13-item trimmed rubric could not reach the target range by trimming alone.
- Based on the latest supplied run set, the pre-expansion rubric sat at Opus `50.6%`, Qwen `47.5%`, spread `3.1%`.
- The safe trim candidate removes former RUB-010, RUB-017, and RUB-018.
- This revision now carries five intended Type B-style additions, including three new near-neighbor diagnostic-denial rungs at RUB-017 through RUB-019.
- Recalibration is required before any discrimination verdict can be claimed for the updated 19-item rubric.

## Intended Type B Additions In This Revision

- Discussion-thread filtering now has an intended positive-control rung: ordinary same-boundary comments stay visible while internal-only marker text remains absent.
- Operator-only diagnostics now have an intended admin-positive-control regression guard so fixes do not over-block admin access.
- Three additional diagnostic-denial rungs now sit close to the existing credential and runtime-introspection items, using slightly varied wording to reward models that cover both caller-class denial and response-body non-leak checks comprehensively.

## Image

- **Tag:** `micro1ai/aspen-yamn-projecthub-flask:v1`
- **Digest:** `sha256:07c109d18f8a365af8caf779ce9f63c3b1796bd00282480cacdcf9025ea74d46`
- **Base commit:** `7d228305d9087ea8cb4784abd51784d687e44109`

## Calibration Results

Pending rerun after the safe trim plus three intended Type B additions. Do not treat earlier 18-item calibration notes as current for this task revision.
