# Deep Dive — `gold-sample-aspen`

> **Audience.** A reader who has *not* seen this repo, this task, or any
> of our internal terminology before. By the end of this document you
> should be able to say (a) what an AI model is being graded on here,
> (b) what the "bug" looks like as code, (c) why a real engineer would
> ship this code in the first place, and (d) why the calibration numbers
> below mean what we say they mean.
>
> The companion `README.md` is a status report for the team — this file
> is the on-ramp for everyone else.

---

## 1. Five-second summary

A frontier AI model is asked to **write a hidden test suite** for a
small FastAPI service that has a real broken-access-control bug. The
agent reviews the code, identifies the leak surface, and authors a test
suite that would catch it — both the leak itself *and* the over-eager
fix shapes that would regress legitimate flows.

We then have an LLM judge read the agent's git diff and check, item by
item, whether the test suite covers each of 13 weighted rubric criteria.
A perfect suite = 1.0; missing everything = 0.0; the per-rubric catch
rate is what we publish.

---

## 2. Why test-authoring is the right shape for this task

The agent's deliverable is **the test suite that codifies the threat
model**, not the fix. That's deliberate:

- **The fix shape is ambiguous in real life.** A correct fix can
  redact private fields in the response, scrub the persisted row at
  storage layer, gate the route at auth, or some combination. None is
  uniquely "correct" — they're trade-offs against different operational
  constraints. Asking the agent to pick a fix shape and then scoring
  them against a hidden test set conflates "which fix did you pick?"
  with "did you understand the threat?"
- **The test suite is unambiguous.** A well-written suite has to catch
  the leak *regardless of which fix shape the implementer chooses*. It
  also has to assert that the legitimate flows still work after a fix
  is applied — i.e., the suite codifies a **dual contract**: "leak
  must be closed" AND "legitimate participant + admin flows must still
  work."
- **This makes the task pure threat-model induction.** The agent isn't
  being graded on engineering taste; they're being graded on whether
  they can articulate what an attacker can exploit and what an
  over-eager fix could regress. Both halves at once.

A separate engineer (human or agent) would later use this test suite
to validate their fix. For that suite to be trustworthy, it
has to (a) catch the actual leak, (b) catch over-blocking fixes, and
(c) not over-specify the fix shape. The rubric checks all three.

---

## 3. The setup — what the agent sees

The agent boots into a small FastAPI service called `taskhub` mounted
at `/repo`. The service is a stand-in for a typical eval-platform's task
/ run / artifact API, with deliberately compact code (~430 LOC total)
so the threat model is enumerable but the centralization argument is
unambiguous.

Three roles:
- **admin** (token `admin-key`) — task author; full read/write
- **alice** (token `user-key`) — participant; can fork tasks, run
  evaluations, share/export her own forks
- **bob** (token `user2-key`) — second participant; same privileges as
  alice, used for cross-author privacy testing

Eight API endpoints across three router files:

| Endpoint | Intended use | Bug |
| --- | --- | --- |
| `GET /tasks/{id}` | Read task metadata | Returns full row including private `sandbox_config.{*_b64, hidden_seed_files}` |
| `GET /coding-tasks` (list) | Browse available tasks | Returns full rows verbatim |
| `GET /tasks/{id}/files/{path}` | Download a seed file | Naive `os.path.join` lets non-admin reach any file in the seed dir, including hidden seeds |
| `GET /tasks/{id}/golden-file/{path}` | Admin-only golden artifact access | Public-by-default route serves `.golden/gold_patch.diff` |
| `POST /tasks/{id}/duplicate` | Fork a task (participant) | Deep-copies private `sandbox_config` into the clone |
| `PATCH /tasks/{id}` | Rename a task | Returns full updated row (laundering surface) |
| `POST /tasks/{id}/share` | Generate share-link payload | Inlines full `sandbox_config` into the response |
| `GET /tasks/{id}/export` | Download fork config as JSON | Returns full task row including private fields |
| `GET /runs/{id}/artifacts*` | Download run artifacts | No `run.model` gate (validation runs leak) and no `created_by` ownership check |
| `GET /tasks/{id}/runs` | List runs for a task | Returns every run including validation runs and other users' runs |

The leak threads through all of these. A correct test suite catches the
leak at *each surface* and asserts that an over-eager fix doesn't break
the legitimate flows: alice can still fork her own task, share her own
fork, export her own fork, run her own evaluations; admin can still see
the full data via the list endpoint.

The agent also sees a small `tests/test_smoke.py` showing the legitimate
participant + admin flows ("alice forks a task," "alice shares her fork,"
"admin creates a task," etc.) — naturalistic integration tests that
encode the route-to-role mapping without saying anything about
redaction or fix shape.

---

## 4. The rubric — what counts as a good test suite

13 weighted rubric criteria, organized into three structural categories:

**Read-side leak coverage** (5 criteria, all major)
1. Non-admin `GET /tasks/{id}` redacts private fields
2. Non-admin `GET /coding-tasks` (list) redacts every row
3. Non-admin `GET /tasks/{id}/files/{name}` 4xx for files in `hidden_seed_files`
4. Non-admin `GET /runs/{id}/artifacts*` 4xx when `run.model` is `*_validation`
5. Non-admin `GET /runs/{id}/artifacts*` 4xx when `run.created_by != caller.user_id`

**Write-side laundering coverage** (3 criteria, all major)
6. Duplicate-then-PATCH laundering — non-admin duplicates a task, PATCHes the clone, asserts no leak in PATCH response
7. Duplicate-then-share laundering — same chain via `/share`
8. Duplicate-then-export laundering — same chain via `/export`

**Anti-overblock regression guards** (5 criteria, varying severity)
9. **Admin GET `/coding-tasks` STILL returns full data** (major)
10. Non-admin participants can still call `/duplicate`, `/share`, `/export` on own resources (major)
11. Non-admin can still download public seed files (minor)
12. Path traversal containment (`..` segments) (minor)
13. Sentinel marker byte tests + zip-content inspection rigor (nitpick)

The "anti-overblock" guards are structurally important. They're why the
test suite has to articulate **both** halves of the dual contract:
"redact for non-admin" AND "preserve admin access." A test author who
writes only the leak-coverage tests, with no anti-overblock guards,
produces a test suite that admits both correct and over-blocking fixes
— it doesn't actually constrain the fix shape.

---

## 5. Why this is realistic

The substrate is deliberately compact (~430 LOC FastAPI service) so the
calibration argument is tight: there's nowhere for a mediocre test
suite to hide. But the *shape* of the bug is real:

- **IDOR / broken access control** is one of the OWASP Top 10 (2021,
  rank A01) and one of the most common vulnerability classes in
  CVE/security advisories.
- **The "convenience read API" pattern** — endpoints that return the
  full database row "for development convenience" and someone forgot to
  redact production-private fields — is a cliché in real-world security
  postmortems.
- **The duplicate-then-X laundering chain** is the form that storage-
  layer privacy bugs take when the application has a "fork" or "clone"
  operation. Every multi-tenant SaaS that lets users fork resources has
  to think about whether the fork inherits private fields from the
  parent; many fail this check on first design.

The agent's job is to **codify the threat model** in a way that catches
the leak, catches over-eager fixes, and survives reviewer scrutiny. That
is a real test-authoring skill, not a synthetic eval artifact.

---

## 6. How calibration runs work

The Aspen pipeline is configured for rubric-judged scoring:

```yaml
# e2b-templates/aspen/pipeline.yaml
name: aspen
check_template: aspen_verify
rubric_only: true
verifier_script: ""
pipeline_type: coding
```

When a task declares `pipeline: aspen` with `ground_truth_issues[]`, the
platform's rubric-only criteria builder auto-generates one
`nl_assertion` criterion per issue. The judge reads the agent's full
trajectory + final diff and scores each criterion against the assertion
text, weighted by severity (`critical=4, major=3, minor=2, nitpick=1`).

The score formula is:
```
reward = sum(score_i * weight_i) / sum(weight_i)
```

For this task, max weight = 35 (10 majors × 3 + 2 minors × 2 + 1 nitpick × 1).

Calibration uses a **per-model saturation-aware escalation ladder**:
- Round 1: n=1 frontier triad (cheap signal — opus, gpt-5.5, gemini)
- Round 2: per-model escalation
  - opus / gpt-5.5: +2 only if their round-1 reward = 1.0 (variance-on-saturation)
  - gemini: +9 always (gemini has historically high variance; n=10 surfaces coverage gradient)

For this calibration, neither opus nor gpt-5.5 hit 1.0 at round 1, so
neither was escalated. Only gemini was extended to n=10 to characterize
its variance distribution.

---

## 7. What the calibration revealed

The full data is in the `README.md`. Three findings worth pulling out
here.

### a. The discrimination ladder is well-behaved

| Tier | Rubric items | Catch rate |
| --- | --- | :---: |
| Frontier-saturated | RUB-008, RUB-010, RUB-002, RUB-011 | ≥58% |
| Mid-tier | RUB-001, RUB-003, RUB-013, RUB-012 | 42–58% |
| Hard | RUB-004, RUB-005, RUB-007, RUB-009 | 25–42% |
| **Top-of-frontier** | **RUB-006** | **8% (1/12)** |

There's a clean ladder from "every model catches" through "hard for
everyone" to "one model in twelve attempts." This is what
discrimination signal looks like — the rubric isn't a flat success/fail
binary; it has structural rungs that different models reach with
different frequencies.

### b. RUB-006 is the unique top-tier rung

Across all 12 attempts (1 opus + 1 gpt-5.5 + 10 gemini), only **one
run** caught RUB-006: gpt-5.5's single round-1 attempt. Opus wrote the
duplicate-then-PATCH chain but skipped the no-leak assertion in the
PATCH response. Gemini didn't write the chain at all in any of its 10
attempts.

What makes RUB-006 hard: it requires the agent to (a) recognize that
PATCH on a cloned task is a serialization site that inherits private
fields from the parent, and (b) write a *chained* test (duplicate →
PATCH → assert) rather than a single-route test. The chain-reasoning is
the discriminator.

This is the sharpest discrimination signal in the rubric. If a future
task wanted another top-tier rung, the structural axis to copy is
"chained write-side laundering with response-shape assertion."

### c. The dual-contract anti-overblock guard (RUB-009)

RUB-009 asks for a test asserting that an **admin** GET `/coding-tasks`
*still* returns rows with private fields — i.e., the test suite must
articulate the dual contract that the fix has to preserve.

RUB-009's 25% catch rate (3/12, all 3 from gemini's n=10 distribution)
is one of the rubric's strongest signals: it's reachable but rare, and
both top-frontier models missed it on first attempt. The "remember the
admin escape hatch" reasoning is a structural property of how frontier
models think about access control — they actively think "redact for
non-admin," but they don't actively verify "preserve admin access."

### d. Per-model failure shapes

**`gpt-5.5`** (best, 0.657): wrote a clean, structurally correct test
suite using a permissive helper `_assert_denied_or_redacted()` that
accepts either 4xx or "200 with no markers." Three of its four misses
(RUB-003, RUB-005) are because the rubric asks for *strict* 4xx but the
helper allows 200 + redacted. RUB-004 is a different miss — didn't gate
on `run.model in {*_validation}` specifically. RUB-009 is the universal
blind spot.

**`gemini-3.1-pro`** (n=10 mean 0.400): strongest model on the
redaction-surface enumeration — passed all 5 of RUB-001 through RUB-005
in ~50–60% of runs. Caught the read-side leak surface reliably. Missed
all the chained workflow tests (RUB-006 PATCH-laundering 0/10, RUB-007
share-laundering 1/10) and got partial coverage on the hygiene tier.

**`claude-opus-4-7`** (single sample 0.486): wrote a more focused but
narrower suite. Missed RUB-001/002 (basic redaction) by indirect
assertion shape — tested via sentinel byte absence rather than `*_b64`
key absence. Missed RUB-005 because it tested cross-user
`/runs/{id}/artifacts/{name}` but forgot the matching `/artifacts-zip`
route. Missed RUB-006 because the PATCH test only asserted the rename
succeeded, never asserted the response omits inherited fields.

---

## 8. How to read the calibration table

In the `README.md`, the per-rubric catch-rate table (`X/12` per rubric)
is the load-bearing data. Three things to look at:

1. **Spread**: max catch rate (75%, RUB-008) minus min catch rate (8%,
   RUB-006) = 0.67. That's the discrimination range — bigger is better
   up to a point (avoiding both saturation and impossibility).
2. **Shape**: ladder rungs across the 13 items? Tier-saturated, mid,
   hard, top? (Answer: yes, four distinct tiers, see §7a above.)
3. **Single model on the top rung**: only gpt-5.5 caught RUB-006. That's
   the strongest within-frontier discrimination signal.

The pass@k table tells you how the score distribution changes with
sampling. Pass@1 = 0.30 means "30% of single attempts cross the 0.5
threshold"; pass@10 = 1.0 means "given 10 attempts, gemini will produce
at least one above-threshold submission." But pass@k under the strict
1.0 threshold collapses to 0 — gemini never reaches a perfect rubric
score on this task.

---

## 9. What this rubric *does not* measure

Worth being explicit:

- **Fix correctness.** The agent isn't fixing the bug — they're testing
  it. A test suite that catches the leak doesn't tell us whether the
  agent *could* fix the leak. (Different task type.)
- **Cross-language test authoring.** The rubric is Python-pytest
  specific. An agent's ability to author equivalent tests in another
  framework (Jest, JUnit) isn't measured here.
- **Over-test risk.** A test suite that asserts overly tight contracts
  (e.g., "the redaction function MUST be named `redact()`") would still
  score well against the rubric but be useless for downstream fix
  authors. The judge scores per-rubric coverage, not real-world test
  utility.
- **Test code quality** (style, naming, DRY-ness). The rubric is a
  threat-model coverage check, not a code-review check.

These are deliberate scope limits. The rubric is calibrated for one
specific question: **does the model articulate the threat model
completely?** Other questions need other tasks.

---

## 10. Glossary

- **rubric_only**: pipeline mode where there's no in-sandbox verifier
  script; the LLM judge scores the agent's submission against per-task
  rubric criteria.
- **ground_truth_issues**: the rubric, encoded as a list of
  `{id, severity, category, description}` entries in `task_config.json`.
  The platform auto-converts each into one `nl_assertion` criterion.
- **nl_assertion**: a criterion that asks the LLM judge to read the
  agent's trajectory and answer "did the agent's submission satisfy
  this assertion?" with a 0/1 score and reasoning text.
- **pass@k**: the HumanEval-style metric `1 − C(n−c, k) / C(n, k)`
  where `n` is total samples, `c` is samples meeting the success
  threshold. Tells you the probability that at least one of `k`
  randomly-drawn samples crosses the threshold.
- **dual contract**: when a single change must satisfy two assertions
  in opposite directions (e.g., "redact for non-admin" *and* "preserve
  admin access"). The defining property of well-calibrated security
  tests; missing one half of the dual contract is the "anti-overblock"
  failure.
- **anti-overblock guard**: a test that fails when an over-eager fix
  removes legitimate functionality alongside the leak. Without these,
  a fix that 403/404s every endpoint scores the same as a correct fix.
- **per-model saturation-aware escalation**: the calibration sampling
  rule. Only escalate models that saturate at round 1 (variance-on-
  saturation); always escalate gemini (variance characterization).
