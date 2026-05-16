---
name: aspen-deliverables
description: "Aspen submission deliverables specifications: prompt.txt (3-paragraph format), task_config.json validation, reasoning.txt (8-15 lines), README.md (calibration data, discrimination verdict), DEEP_DIVE.md (outsider on-ramp), pre-submission checklist. Load when writing or reviewing any of the six submission artifacts."
user-invocable: false
---

# Realm Aspen: Deliverables

## What You Submit

After calibration succeeds and peer QC passes, share your task folder in your private group chat with the Ops team.

```
aspen__taskhub_idor_001/
├── prompt.txt          Engineer-to-engineer query, ~3 paragraphs
├── task_config.json    Pipeline metadata, ground_truth_issues[]
├── reasoning.txt       Threat model + rubric structure rationale
├── README.md           Team-facing status — calibration data lives here
├── DEEP_DIVE.md        Outsider on-ramp
└── image_build/        Docker build context
```

In addition: Docker image pushed to `micro1ai/` private registry with digest in `task_config.json`, and calibration data in `README.md`.

## Per-File Specifications

### prompt.txt

3-paragraph engineer-to-engineer prompt. Frame as a peer asking the agent to write a test suite:

- The reported leak (briefly, without giving away the rubric structure).
- Where to put the tests (e.g., `tests/exfiltration/`).
- Do not modify any file under `{substrate}/`.
- Submission format: unified diff via `submit_answer`.

**Describe symptoms, not the audit plan.** Do not enumerate every route family, endpoint type, module, or vulnerability class. Do not list rubric items.

### task_config.json

- All file paths resolve on disk.
- `rubric_max_score` equals Σ(severity_weight × count).
- `repo.image_digest` matches the pushed image.
- No placeholder strings.
- `submission.expected_diff_paths` matches what the prompt asks the agent to produce.

### reasoning.txt

Concise (8–15 lines) technical justification:

- What the seeded vulnerability is, in plain language.
- Why test-authoring (not bug-fixing) is the right shape for this threat model.
- How the rubric decomposes along the scenario's structural axes — give counts.
- How severity weights map to rubric counts to produce `rubric_max_score`.

### README.md

Team-facing status report. Required sections:

- Tasks-in-this-pack table (substrate, rubric items, status).
- Calibration results — per-model summary table with mean reward, saturation rate, pass-rate, distribution.
- Per-rubric catch rates over N=12.
- Discrimination ladder rung breakdown.
- Discrimination verdict (`DISCRIMINATIVE` / `UNDER-CALIBRATED` / `FLAKY`) with rationale.
- Image tag and digest.

### DEEP_DIVE.md

Outsider on-ramp explaining the codebase and scenario. Include:

- Five-second summary.
- Why test-authoring is the right shape for this scenario (the dual-contract argument).
- What the agent sees — substrate walkthrough.
- What the scenario looks like as code, and why a real engineer might find it worth testing.
- How the rubric items decompose the scenario.
- How to read the calibration numbers.

## Pre-Submission Checklist

- [ ] Folder named `aspen__{substrate}_{descriptor}_{NNN}`
- [ ] All six required artifacts are present
- [ ] `rubric_max_score` arithmetic verified
- [ ] Image tag, digest, and `task_config.json` agree
- [ ] Image is PRIVATE on Docker Hub
- [ ] Calibration data in `README.md`, verdict = `DISCRIMINATIVE`
- [ ] Top-of-frontier rung exists in the per-rubric catch table
- [ ] Prompt does NOT enumerate rubric items or list structural axes
- [ ] Prompt does NOT point directly to suspicious route families or inspection locations
- [ ] No old pipeline-name strings (`shield`/`sequoia`/`hornbeam`) in commit messages, git config, file headers
- [ ] Peer QC passes on file structure, rubric atomicity, and discrimination verdict
