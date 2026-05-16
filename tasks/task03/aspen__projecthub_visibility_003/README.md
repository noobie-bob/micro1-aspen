# aspen__projecthub_visibility_003

## Tasks in this pack

| Substrate | Stack | Rubric items | Max score | Status |
|-----------|-------|--------------:|----------:|--------|
| projecthub | Go `net/http` | 15 (5 critical, 8 major, 1 minor, 1 nitpick) | 52 | REWRITTEN — local rebuild and calibration pending |

## Substrate summary

ProjectHub is a role-based Go HTTP service with teams, projects, tasks, comments, attachments, sharing, reports, and operational tooling. The seeded scenario is a visibility problem that spans core boundary checks, response shaping, delegated access, diagnostic surfaces, and crafted-input paths rather than one isolated route bug.

The service is intentionally small enough to read in one sitting, but wide enough to force real threat-model induction. The legitimate product contract includes same-team participant work, team-lead flows, delegated access, reporting, and broader admin visibility; the task only works if those positive flows stay intact while the leaks are pinned down.

**Vulnerability classes:** CWE-284, CWE-639, CWE-200, CWE-862, CWE-915, CWE-22, CWE-78, CWE-918, CWE-328, CWE-209, CWE-1295.

## Image

- **Tag:** `micro1ai/aspen-projecthub:visibility-v4`
- **Digest:** `sha256:b312cfa2df697d39d5ced97700dc629990705459da32a4a1124332de2a3bdc66`
- **Base commit:** `813e0a3dfd9df8d3aa5603d8588798c968427afd`
- **Status:** published; image digest and base commit updated

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
| RUB-001 | critical | boundary_journey | TBD | TBD |
| RUB-002 | critical | response_shaping | TBD | TBD |
| RUB-003 | critical | delegated_scope | TBD | TBD |
| RUB-004 | critical | operational_surfaces | TBD | TBD |
| RUB-005 | critical | unsafe_inputs | TBD | TBD |
| RUB-006 | major | mutation_integrity | TBD | TBD |
| RUB-007 | major | token_properties | TBD | TBD |
| RUB-008 | major | special_visibility_scope | TBD | TBD |
| RUB-009 | major | artifact_consistency | TBD | TBD |
| RUB-010 | major | widened_summaries | TBD | TBD |
| RUB-011 | major | role_scoped_boundaries | TBD | TBD |
| RUB-012 | major | error_sanitization | TBD | TBD |
| RUB-013 | major | regression_guards | TBD | TBD |
| RUB-014 | minor | repeatability | TBD | TBD |
| RUB-015 | nitpick | test_quality | TBD | TBD |

## Discrimination ladder rung breakdown

| Rung | Intended role | Current count | Notes |
|------|---------------|--------------:|-------|
| Floor | Baseline access and regression items | TBD | Likely to include `boundary_journey` and parts of `regression_guards` if the smoke surface is clear |
| Mid-tier | Strong-model catches without saturation | TBD | Expected candidates: `response_shaping`, `special_visibility_scope`, `widened_summaries`, `error_sanitization` |
| Hard rungs | Frontier-skewed multi-step reasoning | TBD | Expected candidates: `delegated_scope`, `operational_surfaces`, `mutation_integrity`, `role_scoped_boundaries` |
| Top-of-frontier | Rare catches, at least one item preferred | TBD | Expected candidates: `token_properties` or `test_quality` |

## Discrimination verdict

PENDING. This rewrite intentionally trades a 39-item checklist for a 15-item journey-based rubric, but the final verdict must wait for real calibration data. Mark it `DISCRIMINATIVE`, `UNDER-CALIBRATED`, or `FLAKY` only after the summary table, pass@k table, and per-rubric catch table are filled with observed results.

## Aspen pipeline notes

- The Docker image is the agent's working environment, not just a runtime artifact.
- There is no in-sandbox verifier, so `task_config.json` and the rubric descriptions must be self-consistent.
- Prompt-level instruction-following matters: the prompt should describe symptoms, not enumerate the audit plan or rubric.
- The task gets most of its difficulty from merged scenario chains, actor switching, readback assertions, and anti-overblock coverage rather than raw endpoint count.
- Rebuild the production image and refresh `repo.base_commit` and `repo.image_digest` before platform submission.
