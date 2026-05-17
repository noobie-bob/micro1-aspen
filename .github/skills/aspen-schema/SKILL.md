---
name: aspen-schema
description: "task_config.json schema reference, substrate taxonomy (hand-authored vs curated public), severity labels (critical/major/minor/nitpick weights), rubric concern categories (access_control, regression_guard, test_quality, etc.). Load when writing or validating task_config.json, choosing severity weights, or selecting rubric categories."
user-invocable: false
---

# Realm Aspen: Schema, Substrate, and Rubric

## task_config.json Schema

| Field | Description |
|---|---|
| `instance_id` | Unique ID, format `aspen__{descriptor}_{NNN}` |
| `pipeline` | Literal value `"aspen"` |
| `task_type` | Literal value `"test_authoring"` |
| `repo.source_url` | For hand-authored substrates, `local://{descriptor}`. For curated GitHub subsets, the public URL. |
| `repo.base_commit` | Full SHA of the buggy starter commit (the single commit inside the image's `.git`). |
| `repo.image_name` | Full Docker Hub path: `micro1ai/aspen-{substrate}:{descriptor}-v{N}` |
| `repo.image_digest` | The sha256 hash of the pushed image. |
| `repo.repo_dir` | Must match `WORKDIR` in the Dockerfile (typically `/repo`). |
| `repo.language` | Primary language of the substrate. |
| `title` | Short human-readable title. |
| `track` | Literal value `"Realm Aspen"` |
| `cwe` | Array of CWE codes. May be empty or omitted for non-security scenarios. |
| `severity` | Task-level severity (`low\|medium\|high\|critical`). Distinct from per-rubric-item severity. |
| `behavioral_prompt` | Pointer to `prompt.txt`. |
| `rubric_only` | Set to `true`. |
| `submission.expected_diff_paths` | Paths under which the agent's diff is expected (e.g., `["tests/exfiltration/"]`). |
| `submission.presentation` | Literal value `"git_diff"` |
| `ground_truth_issues` | Array of rubric items, each with `id`, `severity`, `category`, `description`. |
| `rubric_max_score` | The weighted sum of all items. Must equal Σ(severity_weight × count). |
| `rubric_severity_weights` | Always `{critical:4, major:3, minor:2, nitpick:1}`. |

## Substrate & Rubric Taxonomy

### Substrate Selection

| Substrate Type | When to use | Notes |
|---|---|---|
| Hand-authored service | Default. ~300–1500 LOC, single carefully scoped target scenario. | Use Flask / FastAPI / Go / Express or similar minimal frameworks. |
| Curated public subset | When a real-world scenario is best illustrated by existing code. | Strip git history, pin to a specific commit, verify a public test suite doesn't already cover it. |

### Concern Categories

Each ground-truth issue is tagged with a category. Two categories apply across every Aspen task:

- **regression_guard:** Anti-overblock items asserting the agent's tests do not fail legitimate operations. **Required in every rubric.**
- **test_quality:** Items measuring assertion rigor beyond status-code checks.

Scenario-dependent categories (pick what naturally decomposes your scenario):

- Security: `access_control`, `ownership`, `redaction`, `traversal`, `sql_injection`, `command_injection`, `ssrf`, `mass_assignment`, `sensitive_data_exposure`, `information_exposure`, `weak_crypto`, `improper_assets`
- Feature coverage: `happy_path`, `error_handling`, `edge_case`
- Regression: `bug_reproduction`, `related_path`

### Severity Labels

| Severity | Weight | When to use |
|---|---|---|
| `critical` | 4 | Items whose absence means the rubric cannot discriminate threat understanding from null knowledge. Use sparingly — 0-3 per task. |
| `major` | 3 | The standard weight for primary coverage and anti-regression guards. Default. |
| `minor` | 2 | Secondary anti-overblock items, peripheral coverage, and adjacent-flow checks. |
| `nitpick` | 1 | Test-quality items — assertion rigor, sentinel markers, and items that reward going beyond surface-level checks. |

### Rubric Structural Groups

Every Aspen rubric must decompose along the scenario's structural axes and include BOTH:

#### Direct-coverage axes
Tests that exercise the target scenario at its primary surface(s). Each distinct manifestation of the scenario is its own rubric item — don't collapse them.

#### Anti-overblock regression guards
Tests asserting legitimate flows still work. Required in every rubric. Shape is scenario-specific:

- **Security/access-control:** Admin still sees the full response; non-admin can still call own-resource write endpoints; public resources remain accessible; action endpoints (duplicate, share, export) still work.
- **Regression:** Test fails on buggy code AND passes on a known-good alternative fix.
- **Feature coverage:** Test asserts on documented behavior, not incidental implementation details.

### Rubric Description Rules (CRITICAL)

**The agent reads `task_config.json`.** Descriptions must be **behaviourally abstract**:

| Leaky element | Why it's bad |
|---|---|
| Field names (`internal_priority`) | Agent searches for these strings directly |
| Endpoint paths (`GET /debug/users`) | Agent hits endpoints without reasoning |
| Attack payloads (`UNION SELECT`) | Agent copies the payload verbatim |
| Vulnerability labels (`SQL injection in search`) | Agent knows exactly what class to test |

**Good:** "A test verifies that a participant can only enumerate resources scoped to their own organisational boundary — cross-boundary resources must be absent from list responses."

**Bad:** "A test asserts that GET /projects returns only projects where team_id matches the caller's team."

**The litmus test:** Could a model write a passing test by copying the description alone, without reading the source code? If yes, the description leaks too much.
