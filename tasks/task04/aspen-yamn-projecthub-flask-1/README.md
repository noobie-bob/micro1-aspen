# aspen__yamn_projecthub_flask

## Substrate Summary

ProjHub is a Flask project-management API with teams, projects, tasks, comments, attachments, search, reports, admin surfaces, and unauthenticated diagnostics. The current rubric focuses on cross-boundary visibility failures, sensitive data exposure, search-query abuse, report command execution, and dual-contract regression guards.

## Current Rubric Shape

| Category | Items | Notes |
|----------|-------|-------|
| redaction | RUB-001 | Privileged field suppression in detail and derived views with an admin positive control |
| sensitive_data_exposure | RUB-006, RUB-011, RUB-012 | Credential exposure via unauthenticated debug/users; seeded-marker absence from config/env surfaces; reachability of debug/env and debug/config without auth |
| regression_guard | RUB-002, RUB-003, RUB-004, RUB-005, RUB-007, RUB-008, RUB-009, RUB-010 | Admin cross-boundary project listing; participant same-team ID traversal; authenticated project list; project share artifact; admin config read; task creation + list read-back; team creation with admin_notes; participant task create + cross-boundary denial |

Severity math: `11×3 + 1×2 = 35`.

## Current Calibration Target

- After rubric redesign, five multi-step regression guards (RUB-004, 005, 007, 009, 010) were replaced with simpler single- or two-call tests that both models should write naturally.
- RUB-008 and RUB-011 are kept as harder items targeting Opus-only passage (Type B).
- Target composition after next evaluation run: `B2 / D10` — ten floor/regression items both models pass, two separation items only Opus passes.
- Projected Opus: ~(10×avg_weight + 2×B_weight) / 35 ≥ 80%; Qwen: ~(10×avg_weight) / 35 in 20–50% band.

## Image

- **Tag:** `micro1ai/aspen-yamn-projecthub-flask:v1`
- **Digest:** `sha256:07c109d18f8a365af8caf779ce9f63c3b1796bd00282480cacdcf9025ea74d46`
- **Base commit:** `7d228305d9087ea8cb4784abd51784d687e44109`
