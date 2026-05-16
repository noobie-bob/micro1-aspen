---
name: aspen-step2
description: "Step 2 walkthrough: write conftest.py shared fixtures and test_smoke.py legitimate-flow tests. Fixture design patterns (reset_state, auth headers, data topology helpers), smoke test coverage requirements (15-25 tests across CRUD/access/search/actions), patterns for Python/Go/Node. Load when writing conftest.py or test_smoke.py."
user-invocable: false
---

# Step 2: Write the Smoke Tests & conftest.py

> **Goal:** Write the load-bearing smoke tests and shared fixtures that encode the service's legitimate-operation surface.

## 2.1 Why Smoke Tests Are Load-Bearing

**The smoke test encodes:**
- Which endpoints exist and what HTTP methods they use
- The route-to-role mapping (which endpoints non-admin participants can call)
- What a successful response looks like for each flow
- The data setup required to exercise each flow

**The smoke test does NOT:**
- Test for any security issues or bugs
- Hint at the rubric structure
- Explicitly list what's broken

## 2.2 Write conftest.py — Shared Fixtures

### Python/pytest Pattern (from task01)

```python
"""Shared test fixtures for {ServiceName}.

Provides Flask test client, auth headers for three roles (admin, user alice,
user bob), and a helper to set up the standard two-team topology.
"""
import pytest
from {substrate}.app import create_app
from {substrate}.db import reset_state


@pytest.fixture()
def app():
    reset_state()
    _app = create_app()
    _app.config["TESTING"] = True
    yield _app


@pytest.fixture()
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture()
def auth_admin():
    return {"Authorization": "Bearer admin-key"}


@pytest.fixture()
def auth_user():
    return {"Authorization": "Bearer user-key"}


@pytest.fixture()
def auth_user2():
    return {"Authorization": "Bearer user2-key"}


@pytest.fixture()
def two_teams(client, auth_admin):
    """Create two teams and assign alice to team-alpha, bob to team-beta.

    Returns: {"alpha": "<team-alpha-id>", "beta": "<team-beta-id>"}
    """
    resp = client.post("/teams", headers=auth_admin, json={
        "name": "team-alpha", "member_ids": ["alice-uuid"],
    })
    assert resp.status_code == 200
    alpha_id = resp.get_json()["id"]

    resp = client.post("/teams", headers=auth_admin, json={
        "name": "team-beta", "member_ids": ["bob-uuid"],
    })
    assert resp.status_code == 200
    beta_id = resp.get_json()["id"]

    return {"alpha": alpha_id, "beta": beta_id}
```

### Key Fixture Design Rules

1. `reset_state()` must be called at the start of every test (via the `app` fixture)
2. Auth fixtures return plain header dicts — dead simple to use
3. Data setup fixtures (like `two_teams`) create the baseline topology all tests share
4. **Document the fixture surface in your prompt** — agents can't infer a hidden conftest

### Go Pattern

```go
// testutil/setup.go
func SetupTestServer(t *testing.T) *httptest.Server {
    t.Helper()
    db := NewInMemoryDB()
    handler := NewRouter(db)
    return httptest.NewServer(handler)
}
```

## 2.3 Write test_smoke.py — Legitimate Flow Tests

### Coverage Requirements (15-25 smoke tests)

| Category | What to Test | Example |
|---|---|---|
| Health / connectivity | Basic endpoint reachability | `test_health`, `test_unauthenticated_returns_401` |
| CRUD (admin) | Admin can create/read/update/delete | `test_admin_creates_team` |
| CRUD (user) | User can operate on own resources | `test_member_creates_project_in_own_team` |
| Access control (legitimate) | User CANNOT create in other team | `test_member_cannot_create_project_in_other_team` |
| Relationships | Creating child resources | `test_member_creates_task_in_own_project` |
| Updates | Patching/transitioning resources | `test_member_updates_own_task` |
| Comments | Adding comments (public + internal) | `test_member_adds_comment` |
| File operations | Upload/download attachments | `test_member_uploads_attachment` |
| Derived operations | Duplicate, share, export | `test_member_duplicates_project` |
| Admin endpoints | Audit log, reports | `test_admin_views_audit_log` |
| Search | Keyword search | `test_member_searches_tasks` |

### Writing Style

```python
"""Smoke tests for {ServiceName} — legitimate participant + admin flows.

These tests encode the codebase's normal-operation surface. They do NOT
test for any security issues.
"""
from __future__ import annotations


def _create_project(client, auth_admin, team_id, name="demo-project"):
    """Helper: admin creates a project under a team."""
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id,
        "name": name,
        "description": "A test project",
    })
    assert resp.status_code == 200
    return resp.get_json()


def test_member_creates_project_in_own_team(client, auth_user, two_teams):
    resp = client.post("/projects", headers=auth_user, json={
        "team_id": two_teams["alpha"],
        "name": "my-project",
        "description": "test",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "my-project"


def test_member_cannot_create_project_in_other_team(client, auth_user, two_teams):
    resp = client.post("/projects", headers=auth_user, json={
        "team_id": two_teams["beta"],  # bob's team
        "name": "cross-team",
    })
    assert resp.status_code in (403, 400)
```

### Anti-Patterns to Avoid

- Do NOT test for the vulnerability (e.g., "test_member_can_see_other_team_projects")
- Do NOT name test functions that hint at the bug class
- Do NOT assert on admin-only field values in non-admin contexts
- Smoke tests should ALL pass against the buggy substrate — they test legitimate flows only
