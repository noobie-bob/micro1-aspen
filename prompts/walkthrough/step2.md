# Step 2: Write the Smoke Tests & conftest.py

> **Goal:** Write the load-bearing smoke tests and shared fixtures that encode the service's legitimate-operation surface. These teach the AI agent how the API works in normal use.

---

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

---

## 2.2 Write conftest.py — Shared Fixtures

The conftest provides reusable fixtures that both the smoke tests AND the agent's test suite will use.

### Pattern: Python/pytest (from task01)

```python
"""Shared test fixtures for {ServiceName}.

Provides Flask test client, auth headers for three roles (admin, user alice,
user bob), and a helper to set up the standard two-team topology used in
all smoke and exfiltration tests.
"""
import pytest
from {substrate}.app import create_app
from {substrate}.db import TEAM_MEMBERS, reset_state


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

    Returns a dict with team IDs:
        {"alpha": "<team-alpha-id>", "beta": "<team-beta-id>"}
    """
    resp = client.post("/teams", headers=auth_admin, json={
        "name": "team-alpha",
        "member_ids": ["alice-uuid"],
    })
    assert resp.status_code == 200
    alpha_id = resp.get_json()["id"]

    resp = client.post("/teams", headers=auth_admin, json={
        "name": "team-beta",
        "member_ids": ["bob-uuid"],
    })
    assert resp.status_code == 200
    beta_id = resp.get_json()["id"]

    return {"alpha": alpha_id, "beta": beta_id}
```

### Key Fixture Design Rules

1. **`reset_state()`** must be called at the start of every test (via the `app` fixture)
2. **Auth fixtures** return plain header dicts — dead simple to use
3. **Data setup fixtures** (like `two_teams`) create the baseline topology that all tests share
4. **Document the fixture surface** in your prompt — agents can't infer a hidden conftest

### For Other Stacks

**Go (testing):**

```go
// testutil/setup.go
func SetupTestServer(t *testing.T) *httptest.Server {
    t.Helper()
    db := NewInMemoryDB()
    handler := NewRouter(db)
    return httptest.NewServer(handler)
}
```

**Express.js (supertest):**

```javascript
// tests/setup.js
const request = require("supertest");
const app = require("../app");

function getClient() {
  return request(app);
}
function adminHeaders() {
  return { Authorization: "Bearer admin-key" };
}
function userHeaders() {
  return { Authorization: "Bearer user-key" };
}

module.exports = { getClient, adminHeaders, userHeaders };
```

**Bun (bun:test):**

```typescript
// tests/helpers.ts
import { describe, expect, test } from "bun:test";
import app from "../server";

export function makeRequest(path: string, headers?: Record<string, string>) {
  return fetch(`http://localhost:3000${path}`, { headers });
}
```

---

## 2.3 Write test_smoke.py — Legitimate Flow Tests

### Coverage Requirements

Your smoke test must cover **every legitimate API surface** the agent will need to understand. Aim for **15-25 smoke tests** covering:

| Category                    | What to Test                        | Example                                                        |
| --------------------------- | ----------------------------------- | -------------------------------------------------------------- |
| Health / connectivity       | Basic endpoint reachability         | `test_health`, `test_unauthenticated_returns_401`              |
| CRUD (admin)                | Admin can create/read/update/delete | `test_admin_creates_team`                                      |
| CRUD (user)                 | User can operate on own resources   | `test_member_creates_project_in_own_team`                      |
| Access control (legitimate) | User CANNOT create in other team    | `test_member_cannot_create_project_in_other_team`              |
| Relationships               | Creating child resources            | `test_member_creates_task_in_own_project`                      |
| Updates                     | Patching/transitioning resources    | `test_member_updates_own_task`                                 |
| Comments                    | Adding comments (public + internal) | `test_member_adds_comment`, `test_admin_adds_internal_comment` |
| File operations             | Upload/download attachments         | `test_member_uploads_attachment`                               |
| Derived operations          | Duplicate, share, export            | `test_member_duplicates_project`                               |
| Admin endpoints             | Audit log, reports                  | `test_admin_views_audit_log`                                   |
| Search                      | Keyword search                      | `test_member_searches_tasks`                                   |

### Writing Style

```python
"""Smoke tests for {ServiceName} — legitimate participant + admin flows.

These tests encode the codebase's normal-operation surface. They are
load-bearing: the agent uses them to induce how the public API behaves
in legitimate use. They do NOT test for any security issues.
"""

from __future__ import annotations
import base64


# ── Helper functions ───────────────────────────────────────────────────
def _create_project(client, auth_admin, team_id, name="demo-project"):
    """Helper: admin creates a project under a team."""
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id,
        "name": name,
        "description": "A test project",
    })
    assert resp.status_code == 200
    return resp.get_json()


def _create_task_in_project(client, headers, project_id, title="demo-task"):
    """Helper: create a task in a project."""
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json={
        "title": title,
        "description": "A test task",
        "priority": "high",
    })
    assert resp.status_code == 200
    return resp.get_json()


# ── Health / basic connectivity ────────────────────────────────────────
def test_health(client):
    """Non-existent resource returns 404, not 500."""
    resp = client.get("/tasks/does-not-exist",
                      headers={"Authorization": "Bearer admin-key"})
    assert resp.status_code != 500


def test_unauthenticated_returns_401(client):
    """Missing auth token yields 401."""
    resp = client.get("/projects")
    assert resp.status_code == 401


# ── Team management (admin) ───────────────────────────────────────────
def test_admin_creates_team(client, auth_admin):
    resp = client.post("/teams", headers=auth_admin, json={
        "name": "eng-team",
        "member_ids": ["alice-uuid"],
    })
    assert resp.status_code == 200
    assert resp.get_json()["id"]


# ── Project CRUD (legitimate flows) ──────────────────────────────────
def test_member_creates_project_in_own_team(client, auth_admin, auth_user, two_teams):
    """Alice (team-alpha member) can create a project in team-alpha."""
    resp = client.post("/projects", headers=auth_user, json={
        "team_id": two_teams["alpha"],
        "name": "alice-project",
    })
    assert resp.status_code == 200


def test_member_cannot_create_project_in_other_team(client, auth_user, two_teams):
    """Alice cannot create a project in team-beta."""
    resp = client.post("/projects", headers=auth_user, json={
        "team_id": two_teams["beta"],
        "name": "should-fail",
    })
    assert resp.status_code == 403

# ... continue for all legitimate flow surfaces
```

---

## 2.4 pytest.ini Configuration

```ini
[pytest]
testpaths = tests
addopts = -v -p no:pretty
```

For other test runners:

**Go:**

```bash
# No config file needed, use `go test ./...`
```

**Jest (Node.js):**

```json
// jest.config.js or package.json > jest
{
  "testMatch": ["**/tests/**/*.test.js"],
  "verbose": true
}
```

---

## 2.5 Validate Smoke Tests Locally

Run the smoke tests locally to confirm they all pass:

```bash
# Python/Flask
cd micro1-aspen/tasks/task02/
pip install -r requirements.txt
pytest tests/test_smoke.py -v

# Expected output:
# tests/test_smoke.py::test_health PASSED
# tests/test_smoke.py::test_unauthenticated_returns_401 PASSED
# tests/test_smoke.py::test_admin_creates_team PASSED
# ... (15-25 tests, all PASSED)
```

### Checklist Before Moving On

- [ ] `conftest.py` provides `app`, `client`, `auth_admin`, `auth_user`, `auth_user2`, and a data-setup fixture
- [ ] `test_smoke.py` has 15-25 tests covering every legitimate API surface
- [ ] All smoke tests pass locally
- [ ] Smoke tests do NOT test for any vulnerabilities/bugs
- [ ] Smoke tests DO demonstrate the route-to-role mapping naturally
- [ ] Helper functions are reusable (the agent's tests will likely import them or replicate the pattern)
- [ ] Comments/docstrings describe what each test verifies without hinting at bugs

---

## 2.6 .dockerignore

Critical: exclude the gold-standard answer and task config from the Docker image:

```dockerignore
# Exclude the gold-standard answer from the Docker image
tests/exfiltration/

# Python caches
**/__pycache__/
**/*.pyc
**/*.pyo

# Task config artifacts (not part of the substrate image)
aspen__*_*/

# Git
.git/
.gitignore
```

This ensures the agent sees only: the service source, the smoke tests, the conftest, and the pytest config — NOT the answer tests or rubric.
