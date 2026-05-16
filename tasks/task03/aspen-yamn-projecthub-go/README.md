# aspen__projecthub_visibility_003

## Tasks in this pack

| Substrate | Stack | Rubric items | Max score | Status |
|-----------|-------|--------------:|----------:|--------|
| projecthub | Go `net/http` | 15 (5 critical, 8 major, 1 minor, 1 nitpick) | 52 | DISCRIMINATIVE — observed Opus N=1 and Qwen N=4 recorded; |

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
| Claude Opus 4.7 | 1 | 0.846 | n/a | n/a | 0.846-0.846 |
| Qwen 3.5 | 4 | 0.423 | n/a | n/a | 0.400-0.470 |
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

## Per-rubric catch rates (observed: Opus N=1, Qwen N=4)

| Rubric | Severity | Category | Opus Catch | Qwen Catch |
|--------|----------|----------|-----------:|-----------:|
| RUB-001 | critical | boundary_journey | 1/1 (100%) | 3/4 (75%) |
| RUB-002 | critical | response_shaping | 1/1 (100%) | 1/4 (25%) |
| RUB-003 | critical | delegated_scope | 0/1 (0%) | 0/4 (0%) |
| RUB-004 | critical | operational_surfaces | 1/1 (100%) | 3/4 (75%) |
| RUB-005 | critical | unsafe_inputs | 1/1 (100%) | 0/4 (0%) |
| RUB-006 | major | mutation_integrity | 1/1 (100%) | 0/4 (0%) |
| RUB-007 | major | token_properties | 0/1 (0%) | 0/4 (0%) |
| RUB-008 | major | special_visibility_scope | 1/1 (100%) | 4/4 (100%) |
| RUB-009 | major | artifact_consistency | 1/1 (100%) | 2/4 (50%) |
| RUB-010 | major | widened_summaries | 1/1 (100%) | 4/4 (100%) |
| RUB-011 | major | role_scoped_boundaries | 1/1 (100%) | 4/4 (100%) |
| RUB-012 | major | error_sanitization | 1/1 (100%) | 0/4 (0%) |
| RUB-013 | major | regression_guards | 1/1 (100%) | 0/4 (0%) |
| RUB-014 | minor | repeatability | 1/1 (100%) | 4/4 (100%) |
| RUB-015 | nitpick | test_quality | 1/1 (100%) | 3/4 (75%) |

## Discrimination ladder rung breakdown

| Rung | Intended role | Current count | Notes |
|------|---------------|--------------:|-------|
| Floor | Both models catch reliably | 8 | Observed floor items are RUB-001, RUB-004, RUB-008, RUB-009, RUB-010, RUB-011, RUB-014, and RUB-015 |
| Mid-tier | Strong-model catches without saturation | 5 | Observed discrimination items are RUB-002, RUB-005, RUB-006, RUB-012, and RUB-013 |
| Hard rungs | Frontier-skewed multi-step reasoning | 2 | Observed hard rungs are RUB-003 and RUB-007; both models missed them in this sample |
| Top-of-frontier | Rare catches, at least one item preferred | 0 | Not yet observed in the current Opus N=1 and Qwen N=4 sample |

## Discrimination verdict

DISCRIMINATIVE, with the current evidence marked as partial rather than final. The observed sample lands at Opus 84.6% and Qwen 42.3%, which is inside the target bands and yields a 42.3-point spread. The task also shows a clean split between eight floor items, five clear Type B discrimination items, and two hard rungs that neither model solved. Gemini and a larger Opus sample are still pending, so this verdict should be treated as the current team-facing status rather than the final platform calibration record.

## Aspen pipeline notes

- The Docker image is the agent's working environment, not just a runtime artifact.
- There is no in-sandbox verifier, so `task_config.json` and the rubric descriptions must be self-consistent.
- Prompt-level instruction-following matters: the prompt should describe symptoms, not enumerate the audit plan or rubric.
- The task gets most of its difficulty from merged scenario chains, actor switching, readback assertions, and anti-overblock coverage rather than raw endpoint count.
- Rebuild the production image and refresh `repo.base_commit` and `repo.image_digest` before platform submission.
