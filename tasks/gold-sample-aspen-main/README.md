# gold-sample-aspen

Reference sample task for the **Aspen** evaluation pipeline — LLM-judge
**test authoring** against curated `ground_truth_issues[]` rubrics.

Aspen is `rubric_only`: there is no in-sandbox verifier and no
`FAIL_TO_PASS` test set. The agent reviews a buggy codebase and authors
the test suite that catches the seeded vulnerability; the LLM judge
scores the agent's git diff against the rubric. The platform converts
each entry in `ground_truth_issues[]` into one `nl_assertion` criterion,
weighted by severity (`critical=4, major=3, minor=2, nitpick=1`), and
the judge scores the agent's submission.

The companion [`DEEP_DIVE.md`](DEEP_DIVE.md) is the on-ramp for readers
who haven't seen this task before. This file is the team-facing status
report.

## Tasks in this pack

| Task | Substrate | Rubric items | Status |
| --- | --- | --- | --- |
| `taskhub_idor` | Hand-authored FastAPI service (~430 LOC) with seeded broken-access-control bug | 13 (10 major + 2 minor + 1 nitpick) | **DISCRIMINATIVE** — calibrated 2026-04-29 |

## Calibration results — `taskhub_idor`

Calibration on Realm Aspen staging task `91441bc4-8286-434c-86c9-83a9dcfad61f`
(2026-04-29). Round 1 = n=1 frontier triad. Round 2 = +9 gemini for
variance characterization (per-model gate: only escalate models that
hit 1.0 at round 1; none of the three saturated, so opus and gpt-5.5
stayed at n=1).

### Per-model summary

| Model | n | Mean | Saturate (=1.00) | Pass-rate (≥0.5) | Distribution |
| --- | :---: | :---: | :---: | :---: | --- |
| `gpt-5.5-2026-04-23` | 1 | **0.657** | 0/1 | 1/1 | {0.657} |
| `gemini-3.1-pro-preview` | 10 | **0.400** | 0/10 | 3/10 | {0.086, 0.229, 0.257, 0.343, 0.429, 0.457, 0.486, 0.514, 0.600, 0.600} |
| `claude-opus-4-7` | 1 | **0.486** | 0/1 | 0/1 | {0.486} |

Frontier-mean spread = **0.257** (gpt-5.5 0.657 vs gemini 0.400). No
model saturates anywhere near 1.0 across 12 total runs; the
13-rubric ceiling is genuinely outside top-frontier reach on this
task.

### gemini-3.1 stability — N=10 pass@k

`pass@k = 1 − C(n − c, k) / C(n, k)` with `n = 10`.

**Success threshold = reward ≥ 0.5** (`c = 3`):

| k | pass@k |
| :---: | :---: |
| 1 | **0.3000** |
| 2 | 0.5333 |
| 3 | 0.7083 |
| 5 | 0.9167 |
| 7 | 0.9917 |
| 10 | 1.0000 |

**Success threshold = reward = 1.0** (`c = 0`):

`c = 0` over N=10 → **pass@k = 0 for all k ∈ [1, 10]**. gemini-3.1
never reaches a perfect rubric score on this task even with 10
attempts; the highest single-run reward across all 12 runs is
`gpt-5.5` at 0.657 (9/13 rubric items).

### Per-rubric catch rates over N=12 (opus 1 + gpt-5.5 1 + gemini 10)

| Rubric | Severity (weight) | Caught | Rate | Notes |
| --- | --- | :---: | :---: | --- |
| RUB-008 (duplicate-export laundering) | major (3) | 9/12 | **75%** | most reliably caught — straightforward serialization-site test |
| RUB-010 (participants can still call write endpoints) | major (3) | 8/12 | **67%** | well-covered (anti-overblock framing in prompt) |
| RUB-002 (list-endpoint redaction) | major (3) | 7/12 | **58%** | strong |
| RUB-011 (public file still downloadable) | minor (2) | 7/12 | **58%** | mostly covered |
| RUB-001 (`GET /tasks/{id}` field redaction) | major (3) | 6/12 | **50%** | strong |
| RUB-013 (sentinel marker bytes + zip-content rigor) | nitpick (1) | 6/12 | **50%** | medium — gemini doesn't think to add markers |
| RUB-003 (per-task hidden_seed_files awareness) | major (3) | 5/12 | **42%** | hard — "per-task awareness" isn't intuitive |
| RUB-012 (path traversal containment) | minor (2) | 5/12 | **42%** | medium |
| RUB-004 (validation-run privacy via `run.model`) | major (3) | 4/12 | **33%** | hard — requires recognizing `*_validation` mode pattern |
| RUB-005 (cross-author run privacy) | major (3) | 4/12 | **33%** | hard — both `/artifacts` and `/artifacts-zip` routes required |
| RUB-007 (duplicate-then-share laundering) | major (3) | 3/12 | **25%** | hard — chained-flow tests |
| **RUB-009 (admin still sees full data)** | **major (3)** | **3/12** | **25%** | **dual-contract anti-overblock** — first-pass blind spot |
| **RUB-006 (duplicate-then-PATCH laundering)** | **major (3)** | **1/12** | **8%** | **top-of-frontier rung** — only gpt-5.5 caught it |

**Per-rubric catch rates over N=10 gemini-only:**

| Rubric | gemini caught | Rate |
| --- | :---: | :---: |
| RUB-008 | 7/10 | 70% |
| RUB-002 | 6/10 | 60% |
| RUB-010 | 6/10 | 60% |
| RUB-001 | 5/10 | 50% |
| RUB-003 | 5/10 | 50% |
| RUB-011 | 5/10 | 50% |
| RUB-005 | 4/10 | 40% |
| RUB-013 | 4/10 | 40% |
| RUB-004 | 3/10 | 30% |
| RUB-009 | 3/10 | 30% |
| RUB-012 | 3/10 | 30% |
| RUB-007 | 1/10 | 10% |
| RUB-006 | 0/10 | **0%** |

**Discrimination ladder rungs:**

- **Frontier-saturated (≥58%)**: RUB-008, RUB-010, RUB-002, RUB-011 — every model catches these reliably
- **Mid-tier (42–58%)**: RUB-001, RUB-003, RUB-013, RUB-012 — ~50/50 across the triad
- **Hard rungs (25–42%)**: RUB-004, RUB-005, RUB-007, RUB-009 — chained workflow + dual-contract reasoning
- **Top-of-frontier (≤10%)**: **RUB-006 (1/12)** — only one frontier model caught the duplicate-then-PATCH laundering chain

**RUB-006 is the unique top-tier rung**: gpt-5.5 was the only model in
12 attempts to write a test that exercises the full duplicate → PATCH
chain *and* asserts the PATCH response omits inherited private fields.
Opus wrote the chain but skipped the assertion; gemini didn't write
the chain at all in any of its 10 attempts. This is the cleanest
discrimination signal in the rubric — a single model, single attempt
across the full N=12 sample.

### Discrimination interpretation

The rubric structure produces a **clean ladder** on this calibration:

- **Frontier ordering**: gpt-5.5 (0.657) > opus (0.486) > gemini (0.400 mean)
- **No saturation, no floor**: max single reward 0.657, min 0.086. Spread 0.571
- **No flakiness**: gemini's n=10 distribution is monotonic and well-behaved (mean 0.400, std ~0.18). Coverage gradient, not noise.
- **Top-tier reachable but rare**: pass@1 (≥0.5) on gemini = 0.30, pass@5 = 0.92. Given enough attempts gemini reliably reaches the mid-tier rungs but never crosses into the top tier.

Verdict: **WITHIN-FRONTIER DISCRIMINATIVE**. The rubric measures
threat-model induction at the test-authoring level — the agent must
articulate what an attacker can exploit *and* what an over-eager fix
could regress, both at once. That dual-contract reasoning is the
structural discriminator.

## Ground-truth rubric — `taskhub_idor`

| ID | Severity | Category | Criterion |
| --- | --- | --- | --- |
| RUB-001 | major | access_control | Test asserts non-admin `GET /tasks/{id}` redacts private `sandbox_config` fields |
| RUB-002 | major | access_control | Test asserts non-admin `GET /coding-tasks` redacts private fields from every row |
| RUB-003 | major | access_control | Test asserts non-admin can't fetch files in `sandbox_config.hidden_seed_files` (per-task awareness) |
| RUB-004 | major | ownership | Test asserts non-admin can't fetch validation-run artifacts (run.model = `*_validation`) |
| RUB-005 | major | ownership | Test asserts non-admin can't fetch cross-author run artifacts |
| RUB-006 | major | redaction | Duplicate-then-PATCH laundering chain |
| RUB-007 | major | redaction | Duplicate-then-share laundering chain |
| RUB-008 | major | redaction | Duplicate-then-export laundering chain |
| RUB-009 | major | regression_guard | **Anti-overblock**: admin GET `/coding-tasks` STILL returns full data |
| RUB-010 | major | regression_guard | **Anti-overblock**: non-admin participants can still call own-resource write endpoints |
| RUB-011 | minor | regression_guard | Anti-overblock: public seed file remains downloadable to non-admin |
| RUB-012 | minor | traversal | Path traversal containment (e.g., `..` segments) |
| RUB-013 | nitpick | test_quality | Sentinel marker bytes + zip-content inspection rigor |

## Per-task contents

```
.
  README.md            # this file — team status report
  DEEP_DIVE.md         # outsider on-ramp: what is being graded, why it works
  prompt.txt           # 3-paragraph engineer-to-engineer ask
  task_config.json     # ground_truth_issues[], image, pipeline=aspen, rubric_only=true
  reasoning.txt        # task design rationale
  image_build/         # per-task Docker context (FastAPI taskhub starter)
```

## Image

`micro1ai/aspen-taskhub-idor:sample-v1` (digest `sha256:eb3c08ebd46399645b2b2cc3ff1f394fb093f7bc9953f012502e3dfa27a40489`).

Build context: `image_build/`. Per the E2B template-builder convention,
the Dockerfile creates uid 1000 literally named `user`, snapshots the
buggy `taskhub/` starter via `git init`, and pins FastAPI + pytest. The
`tests/test_smoke.py` shows the legitimate participant + admin flows
naturalistically — it's what tells the agent which routes are
participant-callable, without prescribing any specific fix shape.

## Aspen pipeline gotchas

- **No deterministic gold validation.** Aspen is `rubric_only: true`;
  there is no `gold_patch.diff` and no `FAIL_TO_PASS` test set. The
  ground truth is the rubric itself.
- **No verifier scripts in the sandbox.** The per-task E2B template is
  the repo image — no verifier upload, no in-sandbox scoring step.
- **`task_config.repo.image_name` is the agent's working environment**,
  not just metadata. The agent reviews the buggy starter live; rubric
  matching happens only at scoring time.
- **Prompt-level instruction-following matters.** A task that says
  "write the test suite" must explicitly forbid code modifications
  (`Do not modify any file under taskhub/`); without that rule frontier
  models will sometimes write a fix instead. The shipped prompt makes
  this constraint explicit.
- **The `tests/test_smoke.py` file in the image is load-bearing.** It
  encodes route-to-role mapping (which endpoints alice/bob can call as
  participants) naturalistically. Removing it floors model performance
  because the agent cannot induce the participant flow from the buggy
  router code alone.

## Verifying on staging

```bash
STAGING_KEY=...
STAGING=https://micro-openenvs-api-staging-502417714596.us-central1.run.app
TASK=91441bc4-8286-434c-86c9-83a9dcfad61f    # canonical taskhub_idor calibration

curl -X POST -H "Authorization: Bearer $STAGING_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"claude-opus-4-7"}' \
     $STAGING/tasks/$TASK/eval
```

Or create your own staging task end-to-end (template build + per-model
sampling) by uploading `task_config.json` + `prompt.txt` to the Realm
Aspen environment `f732a4c8-6a0f-4f5c-8ff9-77b39360c02e` and triggering
`build-coding-task`.

## Related repos

- [`jacky-micro1/gold-sample-hornbeam`](https://github.com/jacky-micro1/gold-sample-hornbeam) — hornbeam reference (rubric-judged PR review)
- [`jacky-micro1/gold-sample-sequoia`](https://github.com/jacky-micro1/gold-sample-sequoia) — sequoia reference (deterministic SWE-bench-style fix)
- [`jacky-micro1/gold-sample-shield`](https://github.com/jacky-micro1/gold-sample-shield) — shield reference (deterministic security fix)
