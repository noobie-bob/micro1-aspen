---
name: aspen-step5
description: "Step 5 walkthrough: calibration targets (Opus ~75-85% N=12, Qwen ~20-50% N=4), harbor CLI commands, rubric adjustment rules (if Opus too high/low, if Qwen too high, if flaky), discrimination ladder, pre-submission checklist, submit to Micro1 platform. Load when calibrating, adjusting rubric after calibration, or submitting."
user-invocable: false
---

# Step 5: Calibration, QC Review & Submission to Micro1

> **Goal:** Run calibration against frontier models, fill in calibration data, pass peer QC, and submit.

## 5.1 Calibration Targets

| Model | Expected Score | Runs |
|---|---|---|
| Claude Opus 4.7 | ~75-85% mean reward | N=12 |
| Qwen 3.5 | ~20-50% mean reward | N=4 |

### What "DISCRIMINATIVE" Means

- Frontier model (Opus) clearly outscores mid-tier model (Qwen)
- Spread of ~0.20 between models
- No saturation (not all models score the same)
- Top-of-frontier rung exists (≥1 item caught only by frontier)

### Verdicts

| Verdict | Meaning | Action |
|---|---|---|
| `DISCRIMINATIVE` | Clear separation ✅ | Ship it |
| `UNDER-CALIBRATED` | Models score similarly or smaller model scores too high | Increase rubric difficulty |
| `FLAKY` | Scores vary wildly within same model | Fix rubric atomicity |

## 5.2 Run Calibration

### Via Harbor CLI

```bash
harbor run -p . -e e2b -a opus-4.7 --runs 12
harbor run -p . -e e2b -a qwen-3.5 --runs 4
```

### Collect Results

After each run, collect:
- Reward score (0.0 to 1.0)
- Per-rubric MET/UNMET for each criterion
- Agent's submitted diff (for analysis)

## 5.3 Fill In Calibration Data in README.md

### Per-Model Summary Table

```markdown
| Model           | N   | Mean Reward | Saturation Rate | Pass Rate | Distribution |
| --------------- | --- | ----------- | --------------- | --------- | ------------ |
| Claude Opus 4.7 | 12  | 0.79        | 0.08            | 0.92      | 0.62–0.92    |
| Qwen 3.5        | 4   | 0.33        | 0.00            | 0.25      | 0.20–0.45    |
```

### Per-Rubric Catch Rates

```markdown
| Rubric  | Category       | Severity | Opus Catch   | Qwen Catch |
| ------- | -------------- | -------- | ------------ | ---------- |
| RUB-001 | access_control | major    | 12/12 (100%) | 3/4 (75%)  |
| RUB-016 | test_quality   | nitpick  | 2/12 (17%)   | 0/4 (0%)   |
```

### Discrimination Ladder

| Rung | Catch Rate | Target Proportion |
|---|---|---|
| Frontier-saturated | ≥ 58% | ~30% of items |
| Mid-tier | 42–58% | ~30% of items |
| Hard rungs | 25–42% | ~25% of items |
| Top-of-frontier | ≤ 10% | ≥ 1 item |

## 5.4 Adjust Rubric Based on Calibration

### If Opus scores too high (>90% consistently)
- Add harder rubric items (sentinel markers, chained flows, alternate serialization paths)
- Increase anti-overblock coverage
- Add items requiring reasoning across multiple files
- Remove prompt hints that name suspicious surfaces directly

### If Opus scores too low (<65%)
- Simplify some rubric items
- Make the prompt slightly more concrete about reported symptoms (not inspection locations)
- Ensure smoke test adequately teaches the API surface

### If Qwen scores too high (>50% consistently)
- Add items requiring deeper code analysis and multi-step reasoning
- Increase proportion of "hard rung" items
- Add more test variety: mutation + read-back, alternate serialization paths, body-level sentinel checks
- Reduce prompt leakage if it points at relevant files or route families
- Remove easy repetitive items instead of just adding more

### If results are FLAKY (high variance)
- Check rubric items for ambiguity — make them more atomic
- Ensure each item is truly binary (MET/UNMET, no interpretation needed)
- Remove items that depend on the agent's specific coding style

### Rubric Reduction Pattern (from task01)

> Started with 28 items, reduced to 16 after Opus 4.7 review:
> 1. Run initial calibration with all items
> 2. Identify redundant items (covered by others)
> 3. Identify ambiguous items (inconsistent MET/UNMET across runs)
> 4. Merge closely related items into single atomic items
> 5. Keep compact set of 11-18 items that cleanly discriminate
> 6. Recalculate `rubric_max_score` after every change

## 5.5 Pre-Submission Checklist

### File Structure

- [ ] `prompt.txt` — 3-paragraph, no rubric enumeration, references `conftest.py` not `test_smoke.py`
- [ ] `task_config.json` — all fields filled, arithmetic correct, no placeholder strings
- [ ] `reasoning.txt` — 8-15 lines, severity distribution explained
- [ ] `README.md` — calibration data, discrimination verdict
- [ ] `DEEP_DIVE.md` — outsider on-ramp
- [ ] `Dockerfile` — E2B convention, anti-cheating

### Technical Verification

- [ ] `rubric_max_score` = Σ(severity_weight × count) — verified
- [ ] `image_name` and `image_digest` match the pushed tag
- [ ] Image is set to PRIVATE on Docker Hub
- [ ] `base_commit` matches the single commit inside the container
- [ ] `expected_diff_paths` matches what the prompt asks the agent to produce
- [ ] No pipeline-name leftovers (no `shield`, `sequoia`, `hornbeam`)
- [ ] Smoke test passes inside the container

### Rubric Integrity

- [ ] Every rubric item is atomic and binary (MET/UNMET)
- [ ] Both direct-coverage AND anti-overblock items present
- [ ] Anti-overblock NOT collapsed into a single item
- [ ] Prompt does NOT enumerate rubric items or structural axes
- [ ] Calibration data shows DISCRIMINATIVE verdict
- [ ] Top-of-frontier rung exists (≥1 item caught <10% of the time)
- [ ] Severity weights: `critical=5, major=3, minor=2, nitpick=1`

### Smoke Test Quality

- [ ] Smoke test encodes the legitimate API surface (route-to-role mapping)
- [ ] Smoke test does NOT test for vulnerabilities/bugs
- [ ] Smoke test does NOT prescribe the scenario-under-test
- [ ] conftest fixtures are documented

## 5.6 Submit to Micro1 Platform

Share your task folder (`aspen__{substrate}_{descriptor}_{NNN}/`) in your private group chat with the Ops team. No ZIP needed.
