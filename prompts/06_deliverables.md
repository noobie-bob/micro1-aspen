# Realm Aspen: Deliverables

## What You Submit

After calibration succeeds and peer QC passes, share your task folder in your private group chat with the Ops team (no ZIP needed).

```
aspen__taskhub_idor_001/
├── prompt.txt          Engineer-to-engineer query, ~3 paragraphs
├── task_config.json    Pipeline metadata, ground_truth_issues[]
├── reasoning.txt       Threat model + rubric structure rationale
├── README.md           Team-facing status — calibration data lives here
├── DEEP_DIVE.md        Outsider on-ramp
└── image_build/        Docker build context
```

In addition:

- **Docker image:** Pushed to `micro1ai/` private registry under a versioned tag, with the digest recorded in `task_config.json`. Set to PRIVATE.
- **Calibration data:** Per-model rewards, pass@k stats, per-rubric catch rates, and the discrimination verdict — all in `README.md`.

## Per-File Specifications

### prompt.txt

3-paragraph engineer-to-engineer prompt. Frame the task as a peer asking the agent to write a test suite for a given scenario. Specify:

- The reported leak (briefly, without giving away the rubric structure).
- Where to put the tests (e.g., `tests/exfiltration/`).
- Do not modify any file under `{substrate}/`.
- Submission format: unified diff via `submit_answer`.

Describe the symptoms, not the audit plan. Do not enumerate every route family, endpoint type, module, or vulnerability class the agent should inspect.

Do not list the rubric items here. The agent must induce what's worth testing from the code, not from the prompt.

### task_config.json

Contains pipeline metadata and the ground truth rubric (See task_config.json Schema section):

- All file paths in the config resolve on disk.
- `rubric_max_score` equals Σ(severity_weight × count).
- `repo.image_digest` matches the pushed image.
- No placeholder strings.
- `submission.expected_diff_paths` matches what the prompt asks the agent to produce.

### reasoning.txt

Threat model and rubric structure rationale. Concise (8–15 lines) technical justification for the task:

- What the seeded vulnerability is, in plain language.
- Why test-authoring (not bug-fixing) is the right shape for this threat model.
- How the rubric decomposes along the scenario's structural axes — give counts.
- How severity weights map to rubric counts to produce `rubric_max_score`.

### README.md

Team-facing status report. Required sections:

- Tasks-in-this-pack table (substrate, rubric items, status).
- Calibration results — per-model summary table with mean reward, saturation rate, pass-rate, distribution.
- gemini N=10 stability — pass@k tables for both reward thresholds.
- Per-rubric catch rates over N=12.
- Discrimination ladder rung breakdown.
- Discrimination verdict (`DISCRIMINATIVE` / `UNDER-CALIBRATED` / `FLAKY`) with rationale.
- Image tag and digest.
- Aspen pipeline gotchas (image is the working env, no in-sandbox verifier, smoke test is load-bearing, prompt-level instruction-following matters).

### DEEP_DIVE.md

Outsider on-ramp explaining the codebase and scenario. Include:

- Five-second summary.
- Why test-authoring is the right shape for this scenario (the dual-contract argument).
- What the agent sees — substrate walkthrough.
- What the scenario looks like as code, and why a real engineer might find it worth testing.
- How the rubric items decompose the scenario.
- How to read the calibration numbers.

### image_build/

The full Docker build context. Must include the Dockerfile, requirements/manifest, the substrate source, the smoke test, the conftest, and any pytest config. The contents of this folder are what gets baked into the pushed image.

## Pre-Submission Checklist

- Folder named `aspen__{substrate}_{descriptor}_{NNN}`.
- All six required artifacts are present.
- `rubric_max_score` arithmetic verified.
- Image tag, digest, and `task_config.json` agree.
- Image is PRIVATE on Docker Hub.
- Calibration data in `README.md`, verdict = `DISCRIMINATIVE`.
- Top-of-frontier rung exists in the per-rubric catch table.
- Prompt does not enumerate rubric items or list the structural axes the agent is expected to find.
- Prompt does not point directly to the suspicious route families or inspection locations beyond the test directory and smoke reference.
- No old pipeline-name strings (no `shield`/`sequoia`/`hornbeam` in commit messages, git config, file headers, etc.).
- Peer QC passes on file structure, rubric atomicity, and discrimination verdict.
