# Step 5: Calibration, QC Review & Submission to Micro1

> **Goal:** Run calibration against frontier models, fill in calibration data, pass peer QC, and submit the completed task to the Micro1 platform.

---

## 5.1 Calibration Targets

Aspen calibrates against specific models to ensure discrimination:

| Model | Expected Score | Runs |
|-------|---------------|------|
| Claude Opus 4.7 | 80%+ (ideally hits 100% at least once) | N=12 |
| Qwen 3.5 | 25-50% range | N=4 (run 4 times) |

### What "DISCRIMINATIVE" Means

A task is **DISCRIMINATIVE** if:
- Frontier model (Opus) clearly outscores mid-tier model (Qwen)
- There's a spread of ~0.20 between models
- No saturation (not all models score the same)
- Top-of-frontier rung exists (≥1 item caught only by frontier)
- Frontier model hits 1.0 (100%) on at least 1 run

### Verdicts

| Verdict | Meaning | Action |
|---------|---------|--------|
| `DISCRIMINATIVE` | Clear separation between models ✅ | Ship it |
| `UNDER-CALIBRATED` | All models score similarly | Increase rubric difficulty |
| `FLAKY` | Scores vary wildly within same model | Fix rubric atomicity |

---

## 5.2 Run Calibration

### Via Harbor CLI

```bash
# Run Opus calibration (N=12)
harbor run -p . -e e2b -a opus-4.7 --runs 12

# Run Qwen calibration (N=4)
harbor run -p . -e e2b -a qwen-3.5 --runs 4
```

### Via Realm Platform

Upload the task to the Realm platform and trigger evaluation runs from the UI.

### Collect Results

After each run, collect:
- **Reward score** (0.0 to 1.0)
- **Per-rubric MET/UNMET** for each criterion
- **Agent's submitted diff** (for analysis)

---

## 5.3 Fill In Calibration Data in README.md

### Per-Model Summary Table

```markdown
| Model | N | Mean Reward | Saturation Rate | Pass Rate | Distribution |
|-------|---|-------------|-----------------|-----------|--------------|
| Claude Opus 4.7 | 12 | 0.82 | 0.25 | 1.00 | 0.65–1.00 |
| Qwen 3.5 | 4 | 0.38 | 0.00 | 0.75 | 0.25–0.50 |
```

### Per-Rubric Catch Rates

```markdown
| Rubric | Category | Severity | Opus Catch | Qwen Catch |
|--------|----------|----------|------------|------------|
| RUB-001 | access_control | major | 12/12 (100%) | 3/4 (75%) |
| RUB-002 | access_control | major | 11/12 (92%) | 2/4 (50%) |
| RUB-003 | access_control | major | 10/12 (83%) | 1/4 (25%) |
| RUB-004 | redaction | major | 9/12 (75%) | 1/4 (25%) |
| RUB-005 | redaction | major | 8/12 (67%) | 0/4 (0%) |
| ...     | ...      | ...    | ...         | ...        |
| RUB-016 | test_quality | nitpick | 2/12 (17%) | 0/4 (0%) |
```

### Discrimination Ladder

Map each rubric item to a rung based on catch rates:

```markdown
| Rung | Description | Catch Rate | Rubric Items |
|------|-------------|------------|--------------|
| Floor (Frontier-saturated) | Any model catches | ≥ 58% | RUB-001, RUB-002, RUB-003 |
| Mid-tier | Strong models catch | 42–58% | RUB-004, RUB-005, RUB-006, RUB-007 |
| Hard rungs | Frontier-only | 25–42% | RUB-008, RUB-009, RUB-010, RUB-011 |
| Top-of-frontier | Rarely caught | ≤ 10% | RUB-016 |
```

### Target Proportions

| Rung | Target % |
|------|----------|
| Frontier-saturated | ~30% of items |
| Mid-tier | ~30% of items |
| Hard rungs | ~25% of items |
| Top-of-frontier | ≥ 1 item |

---

## 5.4 Adjust Rubric Based on Calibration

### If Opus scores too high (>95% consistently)
- Add harder rubric items (sentinel markers, chained flows)
- Increase the anti-overblock coverage
- Add items that require reasoning across multiple files

### If Opus scores too low (<60%)
- Simplify some rubric items
- Make the prompt slightly more directive (still don't list rubric items)
- Ensure the smoke test adequately teaches the API surface

### If Qwen scores too high (>50% consistently)
- Add items requiring deeper code analysis
- Add items requiring multi-step reasoning
- Increase the proportion of "hard rung" items

### If results are FLAKY (high variance)
- Check rubric items for ambiguity — make them more atomic
- Ensure each item is truly binary (MET/UNMET, no interpretation needed)
- Remove items that depend on the agent's specific coding style

### Rubric Reduction Pattern (from task01 experience)

> In task01, we started with **28 rubric items** and reduced to **16** after Opus 4.7 review. The reduction process:
> 1. Run initial calibration with all 28 items
> 2. Identify items that are redundant (covered by other items)
> 3. Identify items that are ambiguous (inconsistent MET/UNMET across runs)
> 4. Merge closely related items into single atomic items
> 5. Keep ~15 items that cleanly discriminate
> 6. Recalculate `rubric_max_score` after every change

---

## 5.5 Pre-Submission Checklist

### File Structure

```
aspen__{substrate}_{descriptor}_{NNN}/
├── prompt.txt              ✅ 3-paragraph, no rubric enumeration
├── task_config.json        ✅ All fields filled, arithmetic correct
├── reasoning.txt           ✅ 8-15 lines, severity distribution
├── README.md               ✅ Calibration data, discrimination verdict
├── DEEP_DIVE.md            ✅ Outsider on-ramp
└── Dockerfile              ✅ E2B convention, anti-cheating
```

### Technical Verification

- [ ] `rubric_max_score` = Σ(severity_weight × count) — verified
- [ ] `image_name` and `image_digest` match the pushed tag
- [ ] Image is set to PRIVATE on Docker Hub
- [ ] `base_commit` matches the single commit inside the container
- [ ] No placeholder strings in `task_config.json`
- [ ] `expected_diff_paths` matches what the prompt asks the agent to produce
- [ ] No pipeline-name leftovers (no `shield`, `sequoia`, `hornbeam`)
- [ ] Smoke test passes inside the container (verified count matches README)

### Rubric Integrity

- [ ] Every rubric item is atomic and binary (MET/UNMET)
- [ ] Both direct-coverage AND anti-overblock items present
- [ ] Anti-overblock is NOT collapsed into a single item
- [ ] Prompt does NOT enumerate rubric items or structural axes
- [ ] Calibration data shows DISCRIMINATIVE verdict
- [ ] Top-of-frontier rung exists (≥1 item caught <10% of the time)
- [ ] Severity weights are calibrated (critical=4, major=3, minor=2, nitpick=1)

### Smoke Test Quality

- [ ] Smoke test encodes the legitimate API surface (route-to-role mapping)
- [ ] Smoke test does NOT test for vulnerabilities/bugs
- [ ] Smoke test does NOT prescribe the scenario-under-test
- [ ] conftest fixtures are documented (or obvious from code)
- [ ] Agent can induce the public API behavior from smoke tests alone

---

## 5.6 Submit to Micro1 Platform

### Upload via Platform

1. Upload the `aspen__{substrate}_{descriptor}_{NNN}/` folder to the Realm platform
2. The platform validates:
   - Docker image builds successfully
   - `task_config.json` schema is valid
   - Image is accessible from the private registry

### Share with Ops Team

Share your task folder in your private group chat with the Ops team (no ZIP needed):

```
aspen__{substrate}_{descriptor}_{NNN}/
├── prompt.txt
├── task_config.json
├── reasoning.txt
├── README.md
├── DEEP_DIVE.md
└── Dockerfile
```

---

## 5.7 Peer QC Review

A peer reviewer will audit before HDM/HDL sign-off:

### What They Check

| Area | Verification |
|------|-------------|
| Rubric atomicity | Each item is MET/UNMET without multi-part interpretation |
| Dual contract | Both direct-coverage AND anti-overblock items present |
| Severity weights | Calibrated and consistent |
| Prompt integrity | No rubric enumeration, no structural axis listing |
| Dockerfile | Anti-cheating (single commit, no remote, fresh git init) |
| Smoke test | Encodes legitimate surface, doesn't prescribe scenario |
| Calibration data | Spread ~0.20, no saturation, top-of-frontier exists |
| Pipeline cleanup | No leftover `shield`/`sequoia`/`hornbeam` strings |

### Common Rejection Reasons

| Reason | Fix |
|--------|-----|
| Single-contract rubric | Add anti-overblock guards |
| Saturated frontier (Opus = 1.00 at n=1) | Add harder rubric items |
| `rubric_max_score` arithmetic error | Recompute: Σ(weight × count) |
| Pipeline-name leftover | Search & remove all references |
| Smoke test missing or anemic | Add 15-25 legitimate-flow tests |
| Prompt leaks the rubric | Rewrite without listing items |

---

## 5.8 Post-Submission Monitoring

After submission and sign-off:

1. **Monitor platform runs** — Check that evaluation runs complete successfully
2. **Review agent submissions** — Look at agent diffs to validate rubric quality
3. **Iterate if needed** — If new issues are found:
   - Increment image version (v2, v3, ...)
   - Update `task_config.json` with new digest
   - **IMPORTANT:** Create a new task on the platform — Realm doesn't pick up config changes to existing tasks

---

## Quick Reference: Complete Project Timeline

| Phase | Time | Key Actions |
|-------|------|-------------|
| **Step 1:** Substrate design & implementation | ~2-3 hrs | Choose service, implement ~300-500 LOC, seed bugs |
| **Step 2:** Smoke tests & conftest | ~1-2 hrs | Write 15-25 legitimate-flow tests, shared fixtures |
| **Step 3:** Docker + prompt + rubric | ~2-3 hrs | Dockerfile, prompt.txt, task_config.json, reasoning.txt |
| **Step 4:** Push + docs + answer tests | ~1-2 hrs | Push image, README.md, DEEP_DIVE.md, gold-standard tests |
| **Step 5:** Calibration + QC + submit | ~2-3 hrs | Run models, fill calibration data, pass QC, submit |
| **Total** | ~8-13 hrs | End-to-end for one task |

---

## Reference Commands Cheat Sheet

```bash
# ── Build & Push ──────────────────────────────────────────────────
docker buildx build --platform linux/amd64 \
  --provenance=false --sbom=false \
  -t micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  --push .

# ── Get Digest ────────────────────────────────────────────────────
docker buildx imagetools inspect \
  micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  --format '{{.Manifest.Digest}}'

# ── Get Base Commit ───────────────────────────────────────────────
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  git rev-parse HEAD

# ── Validate Smoke Tests ─────────────────────────────────────────
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  pytest tests/test_smoke.py -v

# ── Validate Git History ─────────────────────────────────────────
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  sh -c "git log --oneline && echo '---' && git remote -v"

# ── Run Harbor Calibration ────────────────────────────────────────
harbor run -p . -e e2b -a opus-4.7 --runs 12
harbor run -p . -e e2b -a qwen-3.5 --runs 4

# ── Rubric Arithmetic Check ──────────────────────────────────────
python -c "
items = {'critical': 0, 'major': 13, 'minor': 2, 'nitpick': 1}
weights = {'critical': 4, 'major': 3, 'minor': 2, 'nitpick': 1}
score = sum(weights[k] * v for k, v in items.items())
print(f'rubric_max_score = {score}')
"
```
