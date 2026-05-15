# aspen__projecthub_visibility_001

## Task Summary

ProjectHub is a compact Go `net/http` API for calibrating LLM-generated security tests around team-scoped project management. The service includes projects, tasks, comments, attachments, export/share/duplicate flows, admin routes, debug routes, legacy routes, search, report generation, webhook notification, and share-link generation.

## How to run

```bash
go test ./...
```

The benchmark uses Go's built-in `testing` package and `net/http/httptest`. No external runner dependency is required.

The final starter image should include only the service source and the load-bearing smoke test. The authored security suite is for local rubric design and calibration and should not be baked into the agent-facing image.

For task03 specifically, the root [tasks/task03/Dockerfile](tasks/task03/Dockerfile) is the local authoring image and may include the full test suite, while [tasks/task03/aspen__projecthub_visibility_001/Dockerfile](tasks/task03/aspen__projecthub_visibility_001/Dockerfile) is the benchmark package image and should ship only `main.go` plus `smoke_test.go`.

## Rubric Shape

| Severity | Count | Weight | Points |
|----------|-------|--------|--------|
| major | 15 | 3 | 45 |
| minor | 2 | 2 | 4 |
| nitpick | 1 | 1 | 1 |

**Rubric max score:** 50

### Category breakdown

| Category | Count | Notes |
|----------|-------|-------|
| access_control / ownership | 4 major | Cross-team list/detail/mutation/attachment coverage |
| redaction | 3 major | Detail views plus bundled export/share/duplicate responses |
| admin / operational surfaces | 2 major | Admin routes plus debug/legacy exposure checks |
| utility hardening | 5 major | Search, report generation, mass assignment, webhook URLs, share-link predictability |
| information_exposure | 1 major | Traversal and panic disclosure |
| regression_guard | 2 minor | Admin breadth and same-team workflow preservation |
| test_quality | 1 nitpick | Sentinel-based body assertions |

## Calibration intent

This revision intentionally moves away from the inflated mock rubric and keeps only the highest-value varied checks. Basic models should catch direct cross-team access-control failures. Stronger models should catch response-body redaction, operational-surface exposure, mass assignment, unsafe utility handling, and weak share-link generation. Frontier-level submissions should also preserve legitimate admin and same-team participant workflows and use sentinel markers rather than status-code-only assertions.

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
