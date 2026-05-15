# Realm Aspen: Schema, Substrate, and Rubric

## task_config.json Schema

Please always refer to the golden sample for a clear example of how a task should be defined/identified. The config file drives both the agent run and the LLM judge. Key fields:

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
| `cwe` | Array of CWE codes the substrate exemplifies. For security scenarios. May be empty or omitted for non-security scenarios (feature coverage, regression, edge case, etc.). |
| `severity` | Task-level severity (`low\|medium\|high\|critical`). Distinct from per-rubric-item severity. |
| `behavioral_prompt` | Pointer to `prompt.txt`. |
| `rubric_only` | Set to `true`. Indicates there is no in-sandbox verification. |
| `submission.expected_diff_paths` | Paths under which the agent's diff is expected (e.g., `["tests/exfiltration/"]`). |
| `submission.presentation` | Literal value `"git_diff"` |
| `ground_truth_issues` | Array of rubric items, each with `id`, `severity`, `category`, `description`. |
| `rubric_max_score` | The weighted sum of all. Must equal Σ(severity_weight × count). |
| `rubric_severity_weights` | Always `{critical:4, major:3, minor:2, nitpick:1}`. |

## Substrate & Rubric Taxonomy

### Substrate Selection

Aspen substrates fall into two shapes. Hand-authored is preferred for new tasks because it gives precise control over the scenario being tested and avoids contamination from publicly available test suites.

| Substrate Type | When to use | Notes |
|---|---|---|
| Hand-authored service | Default. ~300–500 LOC, single carefully scoped target scenario, hand-authored conftest + smoke test. | Use FastAPI / Flask / similar minimal frameworks. |
| Curated public subset | When a real-world scenario is best illustrated by code that already exists. | Strip git history, pin to a specific commit, verify a public test suite covering the same scenario isn't already searchable. |

### Concern Categories

Each ground-truth issue is tagged with a category. The category vocabulary is scenario-dependent — pick categories that match your scenario's structural axes. Two categories that apply across every Aspen task:

- **regression_guard:** Anti-overblock items to assert that the agent's tests do not fail when legitimate operations are performed. Required in every Aspen rubric.
- **test_quality:** Items that measure the rigor of these assertions beyond status-code or surface checks. Tests should verify the actual observable behavior the scenario demands.

Beyond those two, your categories depend on the scenario. Pick what naturally decomposes your scenario; if a finding doesn't fit any of your categories, the rubric item is probably not atomic:

- The gold sample (a security/access-control scenario) uses categories like `access_control`, `ownership`, `redaction`, `traversal`.
- A feature-coverage scenario might use `happy_path`, `error_handling`, `edge_case`.
- A regression scenario might use `bug_reproduction`, `related_path`.

### Severity Labels

Each rubric item carries a severity. Use the standard weights and apply them as below.

| Severity | Weight | When to use |
|---|---|---|
| `critical` | 4 | Reserved for when missing this item means the rubric cannot discriminate threat understanding from null knowledge. Most Aspen tasks have zero critical items. |
| `major` | 3 | The standard weight for primary coverage and anti-regression guards. Default. |
| `minor` | 2 | Secondary anti-overblock items, peripheral coverage, and adjacent-flow checks. |
| `nitpick` | 1 | Test-quality items — assertion rigor, sentinel markers, and other items that reward going beyond surface-level checks. |

### Rubric Structural Groups

Every Aspen rubric should decompose along whatever structural axes the scenario has. Every rubric must include both direct-coverage items and anti-overblock items. Below is the gold sample's decomposition as one worked example.

#### Direct-coverage axes

Tests that exercise the target scenario at its primary surface(s). For a feature-coverage scenario, direct-coverage might be one axis (the happy path) plus an error-handling axis. Each distinct way the scenario manifests is its own rubric item - don't collapse them.

#### Anti-overblock regression guards

Tests that assert legitimate, scenario-adjacent flows still work. These are the dual-contract items, and they are required in every Aspen rubric. A rubric without anti-overblock guards is trivially satisfied by any test suite that over-asserts and would fail correct alternative implementations.

The shape of anti-overblock items is scenario-specific. For the gold sample's access-control task, the required guards were:

- **Admin still sees the full response.** Catches test suites that scrub responses unconditionally instead of role-conditionally.
- **Non-admin can still call own-resource write endpoints.** Catches test suites that admin-gate the entire write surface.
- **Public resources remain accessible to non-admin.** Catches test suites that over-deny on the public read surface.

For other scenarios, the equivalent anti-overblock guards differ — for a regression test, it might be "the test fails on the buggy code AND passes on a known-good alternative implementation that fixes the bug differently than expected"; for feature coverage, it might be "the test asserts on the documented behavior, not on incidental implementation details that a refactor would change." The constant is: the rubric must include items that catch over-specification.
