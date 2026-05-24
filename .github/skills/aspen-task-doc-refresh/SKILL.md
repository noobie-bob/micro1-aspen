---
name: aspen-task-doc-refresh
description: "Refresh Aspen task docs from task_config.json and the gold-sample-aspen-main reference. Use when updating README.md, DEEP_DIVE.md, or reasoning.txt to the exact gold-sample format, including calibration tables, pass@k, discrimination verdicts, scenario-as-code walkthroughs, reasoning.txt threat-model summaries, or 'How to read the calibration numbers' sections; also use when adding 1-2 line rubric justifications to ground_truth_issues[] in task_config.json for a task folder. Keywords: Aspen task docs, gold-sample, README, DEEP_DIVE, reasoning.txt, pass@k, discrimination verdict, calibration numbers, scenario as code, task_config justification, rubric rationale."
user-invocable: false
---

# Aspen Task Doc Refresh

## What This Skill Produces

This skill updates an Aspen task's documentation so the task folder is internally consistent and aligned to the repo's gold sample.

Typical outputs:

- refreshed `reasoning.txt` in the same compact shape as `tasks/gold-sample-aspen-main/reasoning.txt`
- refreshed `README.md` as the full team-facing status report in the same shape as `tasks/gold-sample-aspen-main/README.md`
- refreshed `DEEP_DIVE.md` as the outsider on-ramp in the same shape as `tasks/gold-sample-aspen-main/DEEP_DIVE.md`
- `task_config.json` rubric entries with short `justification` fields when requested

This skill is for exact-format doc refreshes, not short summaries. If the current `README.md` only contains task metadata, rubric math, or test-author notes, that is incomplete; rebuild it into the gold-sample status-report format instead of preserving the abbreviated shape.

## When to Use

Use this skill when you need to:

- align a task's `reasoning.txt`, `README.md`, and `DEEP_DIVE.md` to `task_config.json`
- rewrite stale docs by following the structure under `tasks/gold-sample-aspen-main/`
- expand a thin `reasoning.txt` into the gold-sample reasoning format with threat-model explanation, rubric decomposition counts, and rubric-max-score math sourced from `task_config.json`
- expand a thin `README.md` into the full calibration status report with tasks-in-this-pack, per-model summary, pass@k, per-rubric catch rates, discrimination ladder, and verdict
- add the missing `How to read the calibration numbers` explanation to `DEEP_DIVE.md`
- expand a marker-inventory section into a real `scenario as code` walkthrough tied to the relevant handler, tool, serializer, or preview path
- add or repair `justification` text for each `ground_truth_issues[]` entry
- clean up mismatches in instance IDs, image metadata, rubric counts, max score, or submission paths

Do not use this skill for calibration math changes unless the calibration data is already available and verified.

## Inputs to Gather

Start from the target task folder. Read only the minimum set needed to ground the updates:

1. target `task_config.json`
2. current `reasoning.txt`
3. current `README.md`
4. current `DEEP_DIVE.md`
5. `tasks/gold-sample-aspen-main/reasoning.txt`
6. `tasks/gold-sample-aspen-main/README.md`
7. `tasks/gold-sample-aspen-main/DEEP_DIVE.md`
8. latest evaluation results if calibration sections are being refreshed
9. one nearby code path that directly computes, serializes, previews, exports, or leaks the scenario's sensitive data

If you need to explain expected rubric values, also inspect the nearby source of truth for seeded values and legitimate behavior, usually:

- substrate seed data (`seed.go`, `seed.py`, fixtures, or equivalent)
- prompt text
- smoke tests
- the handler or tool path that returns the value being asserted

When the user provides newer eval results, treat those as the source of truth for pass tables and verdicts. Do not reuse old sample numbers.

## Procedure

### 1. Anchor on the task folder

Identify the exact task directory first, then work locally from:

- `task_config.json`
- the docs being refreshed
- the nearest seed or smoke-test files needed to justify expected values

Treat `task_config.json` as the authoritative source for title, image metadata, rubric counts, severity weights, submission path, and rubric categories.

Treat `ground_truth_issues[]` in `task_config.json` as the authoritative source for the current rubric's structural content. When refreshing `reasoning.txt`, derive the scenario decomposition, per-group counts, and total score math from the actual rubric entries instead of preserving stale summaries.

### 2. Refresh `reasoning.txt`

Use `tasks/gold-sample-aspen-main/reasoning.txt` as the shape reference. Match its compact style: usually two dense paragraphs totaling about 8-15 lines, not a bullet list and not a one-paragraph stub.

Required `reasoning.txt` shape:

```text
Paragraph 1:
- plain-language description of the seeded vulnerability or regression surface
- why test-authoring is the right evaluation shape for this threat model
- what kinds of leak and anti-overblock behaviors the agent's tests must capture

Paragraph 2:
- how the current rubric decomposes into structural groups
- exact counts per group derived from `ground_truth_issues[]`
- severity-weight arithmetic derived from `rubric_severity_weights` and `rubric_max_score`
```

`reasoning.txt` requirements to enforce:

- Follow the gold-sample compact prose shape rather than a loose summary.
- Name the current task's real vulnerability surfaces and legitimate-flow guards using the task's actual rubric and nearby code, not generic Aspen boilerplate.
- Derive rubric groups and counts from the current `task_config.json` entries. If the rubric has 13 items, the reasoning must reconcile to those 13 items.
- Recompute and state the score math from `rubric_severity_weights` and `rubric_max_score`; do not reuse counts or totals from another task.
- If the current rubric changed, rewrite the decomposition paragraph completely instead of patching isolated numbers.

### 3. Refresh `README.md`

Use `tasks/gold-sample-aspen-main/README.md` as the shape reference. Match its section order and table types as closely as the target task's data allows. Do not collapse it into a metadata stub.

Required `README.md` structure:

```markdown
# <task-pack-name>

<2 short orientation paragraphs: Aspen rubric_only context + README as team-facing status report>

## Tasks in this pack
| Task | Substrate | Rubric items | Status |

## Calibration results — `<task_name>`

### Per-model summary
| Model | n | Mean | Saturate (=1.00) | Pass-rate (>=0.5) | Distribution |

### <model> stability — N=<n> pass@k
`pass@k = 1 - C(n - c, k) / C(n, k)`

### Per-rubric catch rates over N=<total>
| Rubric | Severity (weight) | Caught | Rate | Notes |

**Discrimination ladder rungs:**
- Frontier-saturated ...
- Mid-tier ...
- Hard rungs ...
- Top-of-frontier ...

### Discrimination interpretation
Verdict: **DISCRIMINATIVE** / **UNDER-CALIBRATED** / **FLAKY**

## Ground-truth rubric — `<task_name>`
## Per-task contents
## Image
## Aspen pipeline gotchas
## Verifying on staging
## Related repos
```

README requirements to enforce:

- Keep the opening prose team-facing: what Aspen is, what is being scored, and that `DEEP_DIVE.md` is the outsider on-ramp.
- Always include the `Tasks in this pack` table, even for a single-task pack.
- Under calibration, include a per-model table for the actual calibrated models. If the latest supplied results are for `Claude Opus 4.7` and `Qwen 3.5`, those rows must appear with their real `n`, mean, saturation count, pass-rate, and distribution.
- Build pass@k tables from the latest evaluation results the user provides. Do not fabricate or backfill pass@k from stale sample data.
- Include the per-rubric catch-rate table over the real aggregate sample size. If the task used `N=12`, say `over N=12`; otherwise keep the same wording and swap in the actual `N`.
- Add the discrimination ladder rung breakdown and a short interpretation paragraph that explains spread, saturation, and the top rung.
- End the calibration interpretation with an explicit verdict line: `DISCRIMINATIVE`, `UNDER-CALIBRATED`, or `FLAKY`, plus a brief rationale grounded in the numbers.
- Keep rubric tables, image metadata, and pipeline notes in README. Move task-author notes, vulnerability narration, and code-walkthrough prose to `DEEP_DIVE.md`.

If calibration data is unavailable or stale, keep the gold-sample section scaffolding but mark those sections as pending latest evaluation results instead of inventing numbers.

### 4. Refresh `DEEP_DIVE.md`

Use `tasks/gold-sample-aspen-main/DEEP_DIVE.md` as the structural reference. Preserve the outsider-on-ramp voice and the numbered walkthrough shape instead of writing a short internal note.

Required `DEEP_DIVE.md` structure:

```markdown
# Deep Dive — `<task-pack-name>`

> Audience note explaining that this file is the outsider on-ramp and README is the team-facing status report.

## 1. Five-second summary
## 2. Why test-authoring is the right shape for this task
## 3. The setup — what the agent sees
## 4. The rubric / scenario as code
## 5. Why this is realistic
## 6. How calibration runs work
## 7. What the calibration revealed
## 8. How to read the calibration numbers
## 9. What this rubric does not measure
## 10. Glossary
```

DEEP_DIVE requirements to enforce:

- Keep the audience blockquote at the top and explicitly point readers to `README.md` for status-report data.
- Section 4 must do more than inventory seeded markers. Walk one concrete code path through the relevant file that directly computes, serializes, previews, exports, or leaks the sensitive data. Show what the vulnerability or regression surface looks like as code and explain why a real engineer would consider that path worth testing.
- For the scenario-as-code walkthrough, prefer the owning abstraction: the handler, tool, serializer, or preview/export helper that actually returns the buggy value. A short, grounded walkthrough of one representative path is better than a broad catalog.
- Section 6 should explain the calibration procedure and score formula for the task's actual eval setup.
- Section 7 should summarize what the latest runs revealed: tiering, hardest rubric items, notable blind spots, or model-specific failure shapes.
- Section 8 must explain how to read the catch-rate table, pass@k table, discrimination ladder, spread, and verdict. Listing only score totals and severity weights is insufficient.
- Keep this file focused on the substrate, threat model, and calibration interpretation. Do not turn it into a second copy of the README tables.

If the current file already uses numbered sections, preserve the numbering and replace thin sections in place so `How to read the calibration numbers` remains a distinct section.

### 5. Add rubric `justification` fields when requested

For each entry in `ground_truth_issues[]`, add a short `justification` field.

Each justification should do two things in 1-2 lines:

- explain why the rubric item matters
- explain how the expected value or marker was determined

Good justifications are anchored in concrete repo evidence, such as:

- seeded names, IDs, or sentinel strings from `seed.*`
- legitimate-flow expectations demonstrated by smoke tests
- admin vs participant behavior shown in auth or handler code
- summary or serialization behavior visible in the returning code path

Prefer phrases like:

- "Validates same-team access and uses the seeded project name from `seed.go` as the canonical marker."
- "Guards against over-blocking by preserving admin visibility of seeded privileged fields."

Do not write vague filler such as "important for security" without tying it to the seeded scenario.

### 6. Preserve the dual contract

When updating docs or justifications, maintain both halves of the task:

- the leak or regression the tests must catch
- the legitimate behavior the tests must preserve

If the task includes same-team access, admin access, or participant happy paths, make sure the docs and rubric commentary do not imply that the correct fix is to deny everything.

### 7. Validate before finishing

After editing:

- verify JSON syntax for `task_config.json`
- confirm severity counts and `rubric_max_score` still match
- remove stale names, old image tags, old commits, or copied calibration tables from other tasks
- ensure `reasoning.txt`, `README.md`, and `DEEP_DIVE.md` agree with `task_config.json`
- ensure `reasoning.txt` uses the gold-sample compact format and its rubric-group counts add up to the live `ground_truth_issues[]`
- ensure `README.md` contains tasks-in-this-pack, per-model summary, pass@k, per-rubric catch rates, discrimination ladder, and an explicit verdict
- ensure `DEEP_DIVE.md` contains a real scenario-as-code walkthrough and a `How to read the calibration numbers` section that interprets the tables
- ensure every new justification is specific to the target task's seeded data

## Decision Points

- If the current docs contain borrowed content from another task, replace it with target-task-specific text instead of patching around it.
- If `reasoning.txt` contains only a high-level summary, rebuild it from the live rubric in `task_config.json` using the gold-sample two-paragraph shape.
- If a rubric item's expected marker is unclear, inspect the seed file or call path before writing the justification.
- If calibration numbers cannot be verified from the task folder or known records, leave them as pending.
- If the user has provided fresh evaluation results, rebuild the pass@k and verdict sections from those results instead of preserving older tables.
- If the calibrated sample size is not 12, preserve the gold-sample presentation but relabel the total `N` accurately.
- If justifications already exist and are correct, keep them and only repair weak, generic, or stale ones.

## Completion Checks

- `reasoning.txt` matches the gold-sample compact format and accurately summarizes the live rubric from `task_config.json`.
- `README.md` matches the gold-sample status-report format and the target task's real metadata.
- `DEEP_DIVE.md` explains the actual substrate and rubric rather than a neighboring task, and includes the missing scenario-as-code plus calibration-reading sections.
- Every requested rubric entry has a concise, evidence-based `justification`.
- No unverified calibration numbers, copied sample-task details, or missing pass tables remain.
- The task folder reads as one coherent package.