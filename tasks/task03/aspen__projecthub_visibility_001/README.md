# aspen__projecthub_visibility_001

## Task Summary

ProjectHub is a compact Go `net/http` API for calibrating LLM-generated security tests around team-scoped project management. The service includes projects, tasks, comments, attachments, export/share/duplicate flows, admin routes, debug routes, legacy routes, search, report generation, webhook notification, and share-link generation.

## How to run

```bash
go test ./...
```

The benchmark uses Go's built-in `testing` package and `net/http/httptest`. No external runner dependency is required.

## Rubric Shape

| Severity | Count | Weight | Points |
|----------|-------|--------|--------|
| major | 28 | 3 | 84 |
| minor | 5 | 2 | 10 |
| nitpick | 1 | 1 | 1 |

**Rubric max score:** 95

### Category breakdown

| Category | Count | Notes |
|----------|-------|-------|
| access_control / ownership | 8 major | Cross-team list/detail/mutation/attachment coverage |
| redaction | 6 major | Project/task detail plus export/share/duplicate bundles |
| admin / debug / legacy | 9 items | Admin routes, debug routes, legacy routes, debug dump |
| injection / validation / crypto | 6 major | Search, report generation, webhook URLs, share-link predictability |
| mass_assignment | 2 major | Task and project admin-only fields |
| information_exposure | 1 major | Panic and error disclosure |
| regression_guard | 4 minor | Admin and same-team legitimate flows |
| test_quality | 1 nitpick | Sentinel-based body assertions |

## Calibration intent

This revision intentionally increases the rubric beyond the original mock by splitting previously bundled items and adding missing high-value coverage for project redaction, project patch ownership, and cross-team attachment access. Basic models should catch direct cross-team access-control failures. Stronger models should catch response-body redaction, admin/debug/legacy exposure, mass assignment, unsafe input handling, and weak share-link generation. Frontier-level submissions should also preserve legitimate admin and same-team participant flows and use sentinel markers rather than status-code-only assertions.

## Calibration results

**Status:** Pending. The rubric and Go test suite have been expanded, but calibration runs have not been executed yet.

| Model | N | Mean Reward | Saturation Rate | Pass Rate | Distribution |
|-------|---|-------------|-----------------|-----------|--------------|
| Claude Opus 4.7 | — | — | — | — | — |
| Qwen 3.5 | — | — | — | — | — |
| Gemini 3.1 Pro | — | — | — | — | — |

## Discrimination ladder

| Rung | Description | Rubric focus |
|------|-------------|--------------|
| Floor | Basic IDOR detection | Cross-team list/detail/mutation failures |
| Mid | Data-level leakage detection | Project/task redaction, admin/debug/legacy exposure |
| Ceiling | Input-handling coverage | Search, report generation, webhook, share-link, path traversal |
| Top-of-frontier | Precision under guard rails | Anti-overblock flows and sentinel-marker assertions |

## Discrimination verdict

**Verdict:** PENDING — requires calibration runs.

The benchmark should be discriminative because the smoke suite teaches only legitimate flows, while high-scoring submissions must inspect response bodies, notice multiple independent exposure channels, and avoid overblocking own-team and admin functionality.
