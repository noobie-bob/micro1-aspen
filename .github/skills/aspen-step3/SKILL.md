---
name: aspen-step3
description: "Step 3 walkthrough: Dockerfile templates for Python/Go/Node/Bun, local image build and validation commands, prompt.txt 3-paragraph format, task_config.json rubric writing (behaviourally abstract descriptions, severity weights, 11-18 items). Load when writing the Dockerfile, prompt.txt, or task_config.json rubric."
user-invocable: false
---

# Step 3: Build the Docker Image, Write the Prompt & Rubric

> **Goal:** Containerize the service with anti-cheating measures, write the agent-facing prompt, and construct a varied rubric (usually 11-18 items).

## 3.1 Write the Dockerfile

E2B convention: uid 1000 named `user`, `WORKDIR /repo`, fresh git init with a single commit.

See [aspen-docker](../aspen-docker/SKILL.md) for complete Dockerfile templates (Python, Go, Node, Bun) and the full push/verify workflow.

## 3.2 Build & Validate the Image Locally

```bash
cd micro1-aspen/tasks/task{NN}/

# Build locally (not pushing yet) — ALWAYS use linux/amd64
docker buildx build --platform linux/amd64 \
  --provenance=false --sbom=false \
  -t micro1ai/aspen-{substrate}:{descriptor}-v1 \
  --load .
```

### Validate Inside the Container

```bash
docker run --rm -it micro1ai/aspen-{substrate}:{descriptor}-v1

# 1. Smoke tests pass (all legitimate flows work)
pytest tests/test_smoke.py -v

# 2. Exactly ONE commit, no remote
git log --oneline
git remote -v

# 3. No answer files leaked
ls tests/exfiltration/ 2>/dev/null   # should be empty/not exist
ls aspen__* 2>/dev/null              # should not exist
```

## 3.3 Write prompt.txt

A **3-paragraph engineer-to-engineer message** asking the agent to write a test suite.

### Template

```
A teammate reported [brief symptom description — what they observed, 
enough context to motivate investigation but not enough to name the bug class].

Your task is to write a test suite that [what the tests should demonstrate].
Put your tests in `tests/exfiltration/`. You may read any file in the repo
but must not modify anything outside `tests/`. Reference the fixtures in
`tests/conftest.py` for the client, auth headers, and data setup helpers.

Submit your work as a unified diff via `submit_answer`.
```

### Prompt Rules

- Describe **symptoms**, not the audit plan
- Do NOT enumerate every route family, endpoint type, module, or vulnerability class
- Do NOT list the rubric items
- Do NOT reference `test_smoke.py` (it doesn't exist in the production image)
- Reference `conftest.py` for available fixtures

## 3.4 Write task_config.json Rubric

### Ground Truth Issues Array

```json
{
  "ground_truth_issues": [
    {
      "id": "RUB-001",
      "severity": "critical",
      "category": "access_control",
      "description": "A test verifies that a participant can only enumerate resources scoped to their own organisational boundary — cross-boundary resources must be absent from list responses. The assertion is structural: it checks resource membership, not just HTTP status."
    },
    {
      "id": "RUB-002",
      "severity": "major",
      "category": "access_control",
      "description": "A test verifies that the detail endpoint for a resource enforces the same organisational boundary as the list endpoint — a participant cannot retrieve another boundary's resource directly by ID."
    },
    {
      "id": "RUB-013",
      "severity": "major",
      "category": "regression_guard",
      "description": "An anti-overblock guard: a test confirms that a participant within the same organisational boundary can still access their own resources through both list and detail endpoints after any fix is applied."
    }
  ]
}
```

### Severity Weights

| Severity | Weight | Typical count |
|---|---|---|
| `critical` | 5 | 0-3 items (reserve for fundamental discrimination) |
| `major` | 3 | Most items — primary coverage + anti-overblock guards |
| `minor` | 2 | Peripheral coverage, secondary anti-overblock |
| `nitpick` | 1 | Assertion rigor, sentinel markers |

### rubric_max_score Calculation

```
rubric_max_score = Σ(severity_weight × item_count_per_severity)
```

Example: 2 critical + 8 major + 3 minor + 2 nitpick = (2×5) + (8×3) + (3×2) + (2×1) = 10 + 24 + 6 + 2 = **42**

### Description Writing Rules

**DO NOT include in descriptions:**
- Specific field names (`internal_priority`, `reviewer_notes`)
- Specific endpoint paths (`GET /debug/users`)
- Attack payloads (`UNION SELECT`, `'; DROP TABLE`)
- Vulnerability labels (`SQL injection`, `IDOR`)
- Sentinel values (`P0-TOP-SECRET`)

**The litmus test:** Could a model write a passing test by copying the description alone, without reading the source code? If yes, rewrite it.

### Rubric Checklist

- [ ] 11-18 items (unless scenario richness justifies more)
- [ ] Both direct-coverage AND anti-overblock items present
- [ ] Anti-overblock NOT collapsed into a single item
- [ ] Every item is atomic and binary (MET/UNMET)
- [ ] No field names, endpoint paths, or payloads in descriptions
- [ ] `rubric_max_score` verified arithmetically
- [ ] `regression_guard` category present
