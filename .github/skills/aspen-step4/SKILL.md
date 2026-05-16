---
name: aspen-step4
description: "Step 4 walkthrough: push Docker image to micro1ai registry (buildx linux/amd64, digest capture, set private), write gold-standard exfiltration tests (sentinel marker pattern, RUB-by-RUB coverage), write README.md calibration tables and DEEP_DIVE.md. Load when pushing images or writing gold-standard answer tests."
user-invocable: false
---

# Step 4: Push Image, Write Gold-Standard Tests & Documentation

> **Goal:** Push the Docker image to micro1ai registry, write the gold-standard answer tests, and write README.md and DEEP_DIVE.md.

## 4.1 Push Docker Image to micro1ai Registry

```bash
docker login
# Enter Docker Hub credentials (must have access to micro1ai org)

cd micro1-aspen/tasks/task{NN}/

docker buildx build --platform linux/amd64 \
  --provenance=false --sbom=false \
  -t micro1ai/aspen-{substrate}:{descriptor}-v1 \
  --push .
```

> **WARNING (Apple Silicon):** Never use plain `docker build`. Always `docker buildx build --platform linux/amd64`.

### Capture Digest and Commit

```bash
# Get image digest
docker buildx imagetools inspect \
  micro1ai/aspen-{substrate}:{descriptor}-v1 \
  --format '{{.Manifest.Digest}}'

# Get base_commit
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v1 \
  git rev-parse HEAD
```

Update `task_config.json`:
```json
{
  "repo": {
    "image_name": "micro1ai/aspen-{substrate}:{descriptor}-v1",
    "image_digest": "sha256:...",
    "base_commit": "..."
  }
}
```

Set image to **PRIVATE** on Docker Hub after first push.

> **Tag Poisoning Warning:** E2B's image cache is sticky. A broken first push permanently poisons that tag. Always increment to `v2` and update `task_config.json`.

## 4.2 Write Gold-Standard Answer Tests

These live in `tests/exfiltration/` and are **excluded from the Docker image** via `.dockerignore`. Purpose: calibration reference and proof that every rubric item is satisfiable.

### Structure

```
tests/exfiltration/
├── __init__.py
├── test_access_control.py     # RUB-001, RUB-002, RUB-003
├── test_redaction.py          # RUB-004, RUB-005, RUB-006
├── test_injection.py          # RUB-007
├── test_debug_endpoints.py    # RUB-008, RUB-009
├── test_mass_assignment.py    # RUB-010, RUB-011
├── test_regression_guards.py  # RUB-013, RUB-014
└── test_quality.py            # RUB-016
```

### Writing Pattern

Every test: (1) set up data via conftest fixtures, (2) perform the action, (3) assert the specific behavior.

```python
"""Cross-team data isolation tests. Covers RUB-001, RUB-002, RUB-003."""
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
    _create_project(client, auth_admin, two_teams["alpha"], "alpha-proj")
    _create_project(client, auth_admin, two_teams["beta"], "beta-proj")

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

## 4.3 Validate Answer Tests

Run gold-standard tests inside the container to confirm they catch the bugs:

```bash
docker run --rm -it \
  -v $(pwd)/tests/exfiltration:/repo/tests/exfiltration \
  micro1ai/aspen-{substrate}:{descriptor}-v1 \
  pytest tests/exfiltration/ -v
```

Expected: direct-coverage tests **FAIL** (catching the bugs), regression_guard tests **PASS** (legitimate flows work).

## 4.4 Write README.md

Required calibration sections (fill after running calibration in Step 5):

```markdown
## Calibration Results

| Model           | N   | Mean Reward | Distribution |
| --------------- | --- | ----------- | ------------ |
| Claude Opus 4.7 | 12  | 0.79        | 0.62–0.92    |
| Qwen 3.5        | 4   | 0.33        | 0.20–0.45    |

## Per-Rubric Catch Rates

| Rubric  | Category       | Severity | Opus Catch   | Qwen Catch |
| ------- | -------------- | -------- | ------------ | ---------- |
| RUB-001 | access_control | major    | 12/12 (100%) | 3/4 (75%)  |
| ...

## Discrimination Verdict: DISCRIMINATIVE
```

## 4.5 Write DEEP_DIVE.md

Include:
- Five-second summary of the task
- Why test-authoring (not bug-fixing) is the right shape
- Substrate walkthrough — what the agent sees
- What the scenario looks like as code
- How rubric items decompose the scenario
- How to read the calibration numbers
