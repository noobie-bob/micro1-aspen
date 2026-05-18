# aspen__yamn_projecthub_flask

## Substrate Summary

ProjHub is a Flask project-management API with teams, projects, tasks, comments, attachments, search, reports, admin surfaces, and unauthenticated diagnostics. The current rubric focuses on cross-boundary visibility failures, sensitive data exposure, search-query abuse, report command execution, and dual-contract regression guards.

## Current Rubric Shape

| Category | Items | Notes |
|----------|-------|-------|
| redaction | RUB-001 | privileged field suppression in detail and derived views with an admin positive control |
| sensitive_data_exposure | RUB-006, RUB-011, RUB-012 | credential and runtime-diagnostic surfaces denied across caller classes with body-level non-leak assertions |
| regression_guard | RUB-002, RUB-003, RUB-004, RUB-005, RUB-007, RUB-008, RUB-009, RUB-010 | admin cross-boundary visibility, same-boundary read/write/action continuity, and admin-positive-control diagnostics |

Severity math: `11×3 + 1×2 = 35`.

## Current Calibration Target

- The rubric is deliberately trimmed to the 12-item guide row: two hard-fail rungs, four discrimination rungs, and six floor/regression rungs.
- All regression-guard coverage is retained; the trim removes non-regression denominator weight and recasts selected guard items into explicit happy-path floors.
- The target composition for reruns is `A2 / B4 / D6`, which is the closest guide-row fit available without trimming regression guards.

## Image

- **Tag:** `micro1ai/aspen-yamn-projecthub-flask:v1`
- **Digest:** `sha256:07c109d18f8a365af8caf779ce9f63c3b1796bd00282480cacdcf9025ea74d46`
- **Base commit:** `7d228305d9087ea8cb4784abd51784d687e44109`
