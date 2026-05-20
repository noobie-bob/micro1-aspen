# aspen__projecthub_visibility_003

## Tasks in this pack

| Substrate | Stack | Rubric items | Max score | Status |
|-----------|-------|--------------:|----------:|--------|
| projecthub | Go `net/http` | 12 (3 critical, 6 major, 2 minor, 1 nitpick) | 35 | Calibration pending |

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

## Rubric (from task_config.json)

| Rubric | Severity | Category |
|--------|----------|----------|
| RUB-001 | critical | command_injection_with_benign_control |
| RUB-002 | critical | comment_visibility |
| RUB-003 | critical | response_shaping |
| RUB-004 | major | initialize_connection |
| RUB-005 | major | module_loading |
| RUB-006 | major | task_update_boundary |
| RUB-007 | major | delete_search_consistency |
| RUB-008 | major | search_boundary |
| RUB-009 | major | asset_fetch |
| RUB-010 | minor | diagnostic_non_leak |
| RUB-011 | minor | repeatability |
| RUB-012 | nitpick | test_quality |

## Discrimination ladder rung breakdown

| Rung | Intended role | Current count | Notes |
|------|---------------|--------------:|-------|
| Floor | Both models catch reliably | n/a | See calibration records for model catch rates |
| Mid-tier | Strong-model catches without saturation | n/a | See calibration records for model catch rates |
| Hard rungs | Frontier-skewed multi-step reasoning | n/a | See calibration records for model catch rates |
| Top-of-frontier | Rare catches, at least one item preferred | n/a | See calibration records for model catch rates |

## Discrimination verdict

DISCRIMINATIVE, with the current evidence marked as partial rather than final. The observed sample lands at Opus 84.6% and Qwen 42.3%, which is inside the target bands and yields a 42.3-point spread. The task also shows a clean split between eight floor items, five clear Type B discrimination items, and two hard rungs that neither model solved. Gemini and a larger Opus sample are still pending, so this verdict should be treated as the current team-facing status rather than the final platform calibration record.

## Aspen pipeline notes

- The Docker image is the agent's working environment, not just a runtime artifact.
- There is no in-sandbox verifier, so `task_config.json` and the rubric descriptions must be self-consistent.
- Prompt-level instruction-following matters: the prompt should describe symptoms, not enumerate the audit plan or rubric.
- The task gets most of its difficulty from merged scenario chains, actor switching, readback assertions, and anti-overblock coverage rather than raw endpoint count.
- Rebuild the production image and refresh `repo.base_commit` and `repo.image_digest` before platform submission.
