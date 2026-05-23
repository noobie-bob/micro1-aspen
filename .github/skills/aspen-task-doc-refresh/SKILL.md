---
name: aspen-task-doc-refresh
description: "Refresh Aspen task docs from task_config.json and the gold-sample-aspen-main reference. Use when updating README.md, DEEP_DIVE.md, or adding 1-2 line rubric justifications to ground_truth_issues[] in task_config.json for a task folder. Keywords: Aspen task docs, gold-sample, README, DEEP_DIVE, task_config justification, rubric rationale."
user-invocable: false
---

# Aspen Task Doc Refresh

## What This Skill Produces

This skill updates an Aspen task's documentation so the task folder is internally consistent and aligned to the repo's gold sample.

Typical outputs:

- refreshed `README.md` as the team-facing status report
- refreshed `DEEP_DIVE.md` as the outsider on-ramp
- `task_config.json` rubric entries with short `justification` fields when requested

## When to Use

Use this skill when you need to:

- align a task's `README.md` and `DEEP_DIVE.md` to `task_config.json`
- rewrite stale docs by following the structure under `tasks/gold-sample-aspen-main/`
- add or repair `justification` text for each `ground_truth_issues[]` entry
- clean up mismatches in instance IDs, image metadata, rubric counts, max score, or submission paths

Do not use this skill for calibration math changes unless the calibration data is already available and verified.

## Inputs to Gather

Start from the target task folder. Read only the minimum set needed to ground the updates:

1. target `task_config.json`
2. current `README.md`
3. current `DEEP_DIVE.md`
4. `tasks/gold-sample-aspen-main/README.md`
5. `tasks/gold-sample-aspen-main/DEEP_DIVE.md`

If you need to explain expected rubric values, also inspect the nearby source of truth for seeded values and legitimate behavior, usually:

- substrate seed data (`seed.go`, `seed.py`, fixtures, or equivalent)
- prompt text
- smoke tests
- the handler or tool path that returns the value being asserted

## Procedure

### 1. Anchor on the task folder

Identify the exact task directory first, then work locally from:

- `task_config.json`
- the docs being refreshed
- the nearest seed or smoke-test files needed to justify expected values

Treat `task_config.json` as the authoritative source for title, image metadata, rubric counts, severity weights, submission path, and rubric categories.

### 2. Refresh `README.md`

Use `tasks/gold-sample-aspen-main/README.md` as the shape reference, not a content template to copy verbatim.

Update the README so it reflects the target task's real data:

- task identity (`instance_id`, title, substrate, stack)
- rubric item counts by severity and `rubric_max_score`
- image tag, digest, and base commit from `task_config.json`
- expected submission path and presentation format
- rubric table derived from `ground_truth_issues[]`
- calibration status only if the numbers are verified

Keep it team-facing. If calibration data is unavailable or stale, explicitly mark calibration as pending instead of inventing numbers.

### 3. Refresh `DEEP_DIVE.md`

Use `tasks/gold-sample-aspen-main/DEEP_DIVE.md` as the structural reference.

Include the sections that explain:

- five-second summary
- why test-authoring is the right task shape
- what the agent sees in the codebase
- what the scenario looks like in code
- how the rubric decomposes the scenario
- what to look for when writing tests
- Aspen pipeline caveats when relevant

Ground the explanation in the actual substrate files and seeded actors, markers, or routes for the target task.

### 4. Add rubric `justification` fields when requested

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

### 5. Preserve the dual contract

When updating docs or justifications, maintain both halves of the task:

- the leak or regression the tests must catch
- the legitimate behavior the tests must preserve

If the task includes same-team access, admin access, or participant happy paths, make sure the docs and rubric commentary do not imply that the correct fix is to deny everything.

### 6. Validate before finishing

After editing:

- verify JSON syntax for `task_config.json`
- confirm severity counts and `rubric_max_score` still match
- remove stale names, old image tags, old commits, or copied calibration tables from other tasks
- ensure README and DEEP_DIVE agree with `task_config.json`
- ensure every new justification is specific to the target task's seeded data

## Decision Points

- If the current docs contain borrowed content from another task, replace it with target-task-specific text instead of patching around it.
- If a rubric item's expected marker is unclear, inspect the seed file or call path before writing the justification.
- If calibration numbers cannot be verified from the task folder or known records, leave them as pending.
- If justifications already exist and are correct, keep them and only repair weak, generic, or stale ones.

## Completion Checks

- `README.md` matches the target task identity and metadata.
- `DEEP_DIVE.md` explains the actual substrate and rubric rather than a neighboring task.
- Every requested rubric entry has a concise, evidence-based `justification`.
- No unverified calibration numbers or copied sample-task details remain.
- The task folder reads as one coherent package.