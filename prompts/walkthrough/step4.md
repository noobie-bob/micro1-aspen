# Step 4: Push Image, Write Gold-Standard Tests & Documentation

> **Goal:** Push the Docker image to micro1ai registry, write the gold-standard answer tests (for calibration), write README.md and DEEP_DIVE.md, and validate everything end-to-end.

---

## 4.1 Push Docker Image to micro1ai Registry

### Login to Docker Hub

```bash
docker login
# Enter your Docker Hub credentials (must have access to micro1ai org)
```

### Build & Push (Single Command)

```bash
cd micro1-aspen/tasks/task02/

docker buildx build --platform linux/amd64 \
  --provenance=false --sbom=false \
  -t micro1ai/aspen-{substrate}:{descriptor}-v1 \
  --push .
```

> **WARNING (Apple Silicon / ARM):** Never use plain `docker build` — it produces arm64 images that silently fail in the pipeline. Always use `docker buildx build --platform linux/amd64`.

### Capture the Image Digest

```bash
docker buildx imagetools inspect \
  micro1ai/aspen-{substrate}:{descriptor}-v1 \
  --format '{{.Manifest.Digest}}'
# Output: sha256:9903e0556fa71aa2840e153238b890395bf24aa92a4948619e81cf300256302d
```

### Update task_config.json

Update these two fields with the exact pushed values:

```json
{
  "repo": {
    "image_name": "micro1ai/aspen-{substrate}:{descriptor}-v1",
    "image_digest": "sha256:9903e0556fa71aa2840e153238b890395bf24aa92a..."
  }
}
```

### Get the base_commit from Inside the Container

```bash
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v1 \
  git rev-parse HEAD
# Output: 3198082a0f243617c1a5b606bf873f0f979477c0
```

Update `task_config.json`:

```json
{
  "repo": {
    "base_commit": "3198082a0f243617c1a5b606bf873f0f979477c0"
  }
}
```

### Set Image to PRIVATE on Docker Hub

1. Go to https://hub.docker.com/r/micro1ai/aspen-{substrate}
2. Settings → Visibility → **Private**

### Known Gotcha: Tag Poisoning

> **E2B's image cache is sticky.** If your first push has the wrong architecture or broken dependencies, that tag is permanently poisoned. You **must** increment the version suffix to `v2` and update `task_config.json`. Never overwrite a tag — always increment.

---

## 4.2 Write Gold-Standard Answer Tests

These are the actual tests that demonstrate what a "perfect" agent submission would look like. They live in `tests/exfiltration/` and are **excluded from the Docker image** via `.dockerignore`.

### Purpose

- Used for **calibration** — running them against the service to verify all rubric items are testable
- Used as the **answer.diff** reference for scoring comparisons
- They serve as proof that every rubric item is satisfiable

### Example Structure (from task01)

```
tests/exfiltration/
├── __init__.py
└── test_info_exposure.py      # Tests for RUB-012 (information exposure)
```

In task01, we ended up with a focused set. For a full answer, you'd typically have:

```
tests/exfiltration/
├── __init__.py
├── test_access_control.py     # RUB-001, RUB-002, RUB-003
├── test_redaction.py          # RUB-004, RUB-005, RUB-006
├── test_injection.py          # RUB-007
├── test_debug_endpoints.py    # RUB-008, RUB-009, RUB-015
├── test_mass_assignment.py    # RUB-010, RUB-011
├── test_info_exposure.py      # RUB-012
├── test_regression_guards.py  # RUB-013, RUB-014
└── test_quality.py            # RUB-016
```

### Writing Pattern for Each Test

Every test should:

1. **Set up the required data** using conftest fixtures
2. **Perform the action** (API call with specific role)
3. **Assert the specific behavior** the rubric item describes

```python
"""Cross-team data isolation tests.

Tests that non-admin users cannot access resources belonging to other teams.
Covers RUB-001, RUB-002, RUB-003.
"""
from __future__ import annotations


def _create_project(client, auth_admin, team_id, name="test-project"):
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id, "name": name, "description": "test",
    })
    assert resp.status_code == 200
    return resp.get_json()


# ── RUB-001: Cross-team list isolation ─────────────────────────────────
def test_non_admin_list_projects_returns_only_own_team(
    client, auth_admin, auth_user, auth_user2, two_teams
):
    """GET /projects as non-admin must return only own-team projects."""
    # Create project in each team
    _create_project(client, auth_admin, two_teams["alpha"], "alpha-proj")
    _create_project(client, auth_admin, two_teams["beta"], "beta-proj")

    # Alice (team-alpha) should only see alpha-proj
    resp = client.get("/projects", headers=auth_user)
    assert resp.status_code == 200
    projects = resp.get_json()

    project_names = [p["name"] for p in projects]
    assert "alpha-proj" in project_names
    assert "beta-proj" not in project_names, (
        "Non-admin can see projects from other teams — IDOR vulnerability"
    )


# ── RUB-013: Anti-overblock regression guard ───────────────────────────
def test_same_team_access_still_works(client, auth_admin, auth_user, two_teams):
    """Anti-overblock: same-team non-admin CAN access own-team resources."""
    project = _create_project(client, auth_admin, two_teams["alpha"])

    resp = client.get(f"/projects/{project['id']}", headers=auth_user)
    assert resp.status_code == 200, (
        "Same-team access blocked — fix over-blocks legitimate flows"
    )
```

### Sentinel Marker Pattern (for test_quality rubric items)

```python
# ── RUB-016: Sentinel marker assertions ────────────────────────────────
def test_sentinel_markers_not_leaked(client, auth_admin, auth_user, two_teams):
    """Seed sentinel bytes into admin-only fields, assert they don't leak."""
    import uuid
    sentinel = f"SENTINEL_{uuid.uuid4().hex[:12]}"

    project = _create_project(client, auth_admin, two_teams["alpha"])

    # Seed sentinel into admin-only field
    client.patch(f"/projects/{project['id']}", headers=auth_admin, json={
        "admin_config": sentinel,
    })

    # Non-admin should NOT see the sentinel anywhere
    resp = client.get(f"/projects/{project['id']}", headers=auth_user)
    body = resp.get_data(as_text=True)
    assert sentinel not in body, (
        f"Sentinel marker '{sentinel}' leaked to non-admin response"
    )
```

---

## 4.3 Validate Answer Tests

Run the gold-standard tests inside the container to verify they properly catch the bugs:

```bash
# Copy answer tests into a running container
docker run --rm -it -v $(pwd)/tests/exfiltration:/repo/tests/exfiltration \
  micro1ai/aspen-{substrate}:{descriptor}-v1 \
  pytest tests/ -v

# Expected: smoke tests PASS, exfiltration tests may PASS or FAIL
# depending on whether they test for bugs that exist (they should FAIL
# against the buggy code for direct-coverage items, PASS for regression guards)
```

### What to Expect

| Test Category                           | Expected Result Against Buggy Code     |
| --------------------------------------- | -------------------------------------- |
| Smoke tests                             | All PASS ✅                            |
| Direct coverage (IDOR, injection, etc.) | FAIL ❌ (bugs exist, tests catch them) |
| Anti-overblock / regression guards      | PASS ✅ (legitimate flows work)        |
| Test quality (sentinel markers)         | FAIL ❌ (leaked data visible)          |

> **Important:** Direct-coverage tests **should FAIL** against the buggy code — that proves they catch the bugs. This is correct behavior.

---

## 4.4 Write README.md

Team-facing status report with calibration data placeholders:

```markdown
# aspen\__{substrate}_{descriptor}\_{NNN}

## Tasks in this pack

| Substrate                            | Rubric Items                        | Max Score | Status                        |
| ------------------------------------ | ----------------------------------- | --------- | ----------------------------- |
| {substrate} ({framework}, ~{N}k LOC) | 16 (13 major + 2 minor + 1 nitpick) | 44        | PUSHED — awaiting calibration |

## Substrate Summary

{2-3 sentence description of the service and its vulnerability classes.}

**Vulnerability classes:** CWE-284, CWE-639, ...

## Image

- **Tag:** `micro1ai/aspen-{substrate}:{descriptor}-v{N}`
- **Digest:** `sha256:...`
- **Base commit:** `{commit-hash}`
- **Status:** Pushed to Docker Hub — set to PRIVATE

## Calibration Results

> **Status:** Pending — calibration runs have not been executed yet.

| Model           | N   | Mean Reward | Saturation Rate | Pass Rate | Distribution |
| --------------- | --- | ----------- | --------------- | --------- | ------------ |
| Claude Opus 4.7 | —   | —           | —               | —         | —            |
| Qwen 3.5        | —   | —           | —               | —         | —            |

### Per-rubric catch rates (N=12)

| Rubric  | Category       | Severity | Opus Catch | Qwen Catch |
| ------- | -------------- | -------- | ---------- | ---------- |
| RUB-001 | access_control | major    | —          | —          |
| ...     | ...            | ...      | —          | —          |

### Discrimination verdict

**Verdict:** PENDING — requires calibration runs.

## Aspen Pipeline Notes

- The Docker image IS the agent's working environment
- The smoke test is load-bearing
- The conftest provides {list key fixtures}
- The prompt does NOT enumerate rubric items
- {N} smoke tests pass in the container (verified)
- Image built with `--provenance=false --sbom=false`
```

---

## 4.5 Write DEEP_DIVE.md

Outsider on-ramp document:

```markdown
# Deep Dive: {Service Name} {Task Title}

## Five-Second Summary

{Service} is a {framework} {type} API with {N}+ endpoints managing {resources}.
The service has seeded vulnerabilities spanning {N} classes. The agent must
author a test suite that catches all of these without over-blocking legitimate flows.

## Why Test-Authoring Is the Right Shape

{The dual-contract argument...}

## What the Agent Sees

{Directory tree of /repo}
{Auth model table}
{Key code patterns to notice — show actual code snippets of bugs}

## How the Rubric Decomposes the Scenario

{Table: category, item count, what it tests}

## How to Read the Calibration Numbers

{Explain mean reward, saturation rate, catch rate, discrimination ladder}
```

---

## 4.6 Final Validation Checklist

- [ ] Docker image pushed with correct tag and set to PRIVATE
- [ ] `task_config.json` has correct `image_name`, `image_digest`, `base_commit`
- [ ] `task_config.json` has no placeholder strings (no "LEAVE_BLANK", etc.)
- [ ] `rubric_max_score` arithmetic double-checked
- [ ] Gold-standard answer tests validate all rubric items
- [ ] Smoke tests pass inside the container
- [ ] No `.git` history beyond single commit
- [ ] No pipeline-name leftovers (no `shield`, `sequoia`, `hornbeam`)
- [ ] README.md has calibration placeholder tables
- [ ] DEEP_DIVE.md explains the scenario for an outsider
- [ ] `prompt.txt` does not enumerate rubric items

### If You Need to Re-push

If anything was wrong with the first push:

```bash
# ALWAYS increment the version number
docker buildx build --platform linux/amd64 \
  --provenance=false --sbom=false \
  -t micro1ai/aspen-{substrate}:{descriptor}-v2 \
  --push .

# Get new digest
docker buildx imagetools inspect \
  micro1ai/aspen-{substrate}:{descriptor}-v2 \
  --format '{{.Manifest.Digest}}'

# Update task_config.json with new tag + digest
# Get new base_commit from inside new container
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v2 git rev-parse HEAD
```
