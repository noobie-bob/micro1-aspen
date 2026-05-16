# Step 1: Design & Build the Substrate Service

> **Goal:** From a blank project, choose your service type, define the scenario (bug, feature, vulnerability), and implement the hand-authored codebase (~300-500 LOC) that the AI agent will review.

---

## 1.1 Choose Your Service & Scenario

Pick a **service type** and a **scenario** (vulnerability, feature, regression, edge case) to test. The service is the "substrate" — the buggy/incomplete codebase the agent will analyze.

### Supported Stacks (examples)

| Stack             | Framework                | When to Use                                    |
| ----------------- | ------------------------ | ---------------------------------------------- |
| Python + Flask    | `flask==3.1.0`           | Security vulns, API testing, rapid prototyping |
| Python + FastAPI  | `fastapi`, `uvicorn`     | Async APIs, type-checked routes                |
| Go                | `net/http`, `chi`, `gin` | Systems-level bugs, concurrency issues         |
| Node.js + Express | `express`                | JS ecosystem, middleware bugs                  |
| Node.js + Bun     | `bun serve`              | Fast runtime, JS/TS edge cases                 |
| Bash server       | `socat`, `ncat`          | Minimal surface, Unix-specific bugs            |
| Elastic           | `elasticsearch`          | Query injection, data exposure                 |

### Scenario Examples

| Scenario Type                  | Example                                 | Categories                                  |
| ------------------------------ | --------------------------------------- | ------------------------------------------- |
| Security (IDOR/access control) | Cross-team data isolation failure       | `access_control`, `ownership`, `redaction`  |
| Security (injection)           | SQL injection, command injection        | `sql_injection`, `command_injection`        |
| Feature coverage               | New payment API contract                | `happy_path`, `error_handling`, `edge_case` |
| Regression guard               | Date parsing bug in timezone conversion | `bug_reproduction`, `related_path`          |
| Edge case                      | Race condition in concurrent writes     | `concurrency`, `data_integrity`             |

### Naming Convention

```
aspen__{substrate}_{vulnerability_class}_{NNN}
```

Examples:

- `aspen__projhub_visibility_001` — Flask project management, visibility vulns
- `aspen__billing_sqli_001` — Billing API, SQL injection
- `aspen__filestore_traversal_001` — File store, path traversal
- `aspen__chatapi_race_001` — Chat API, race condition

---

## 1.2 Scaffold the Directory Structure

Create this folder structure inside `micro1-aspen/tasks/taskNN/`:

```
micro1-aspen/tasks/task02/
├── .dockerignore                    # Exclude answer files from image
├── Dockerfile                       # Agent's isolated environment
├── requirements.txt                 # (or package.json, go.mod, etc.)
├── pytest.ini                       # (or test runner config)
├── {substrate}/                     # Your service source code
│   ├── __init__.py                  # (language-dependent)
│   ├── app.py                       # App factory / entry point
│   ├── auth.py                      # Auth module
│   ├── db.py                        # Data layer
│   └── routes/                      # Route modules
│       ├── __init__.py
│       ├── feature_a.py
│       ├── feature_b.py
│       └── debug.py                 # (if applicable)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures (include in production image)
│   └── test_smoke.py                # Load-bearing legitimate flow tests (remove for production image)
└── aspen__{substrate}_{vuln}_{NNN}/ # Task config directory
    ├── prompt.txt
    ├── task_config.json
    ├── reasoning.txt
    ├── README.md
    ├── DEEP_DIVE.md
    └── Dockerfile                   # Copy of root Dockerfile
```

---

## 1.3 Implement the Service (~300-500 LOC)

### Key Principles

1. **Seed the bugs intentionally** — Every vulnerability/scenario must be deliberate and precisely scoped
2. **Keep it self-contained** — In-memory storage, no external database dependencies
3. **Use realistic patterns** — The code should look like real production code that has bugs, not toy code

### Example: Flask Service (from task01 — ProjHub)

**`app.py`** — App factory with error handlers:

```python
"""Flask application factory for {ServiceName}."""
import traceback
from flask import Flask, jsonify
from {substrate}.db import reset_state
from {substrate}.routes import feature_a, feature_b, debug

def create_app() -> Flask:
    reset_state()
    app = Flask(__name__)
    app.config["TESTING"] = False

    # Register blueprints
    app.register_blueprint(feature_a.bp)
    app.register_blueprint(feature_b.bp)
    app.register_blueprint(debug.bp)

    # BUG: Verbose error handler leaks internals
    @app.errorhandler(Exception)
    def handle_exception(e):
        tb = traceback.format_exc()
        return jsonify({"error": str(e), "traceback": tb}), 500

    return app

app = create_app()
```

**`auth.py`** — Static bearer-token auth (3 roles minimum):

```python
VALID_TOKENS = {
    "admin-key":  ("admin", "admin-uuid"),
    "user-key":   ("user",  "alice-uuid"),
    "user2-key":  ("user",  "bob-uuid"),
}
```

**`db.py`** — In-memory storage with `reset_state()`:

```python
TEAMS: dict[str, dict] = {}
PROJECTS: dict[str, dict] = {}
# ... other tables

def reset_state() -> None:
    """Wipe all storage. Called at app startup and from tests."""
    TEAMS.clear()
    PROJECTS.clear()
    # ...
```

### For Other Stacks

**Go:**

```go
// main.go
package main
import "net/http"
func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/api/items", handleItems)
    http.ListenAndServe(":8080", mux)
}
```

**Express.js:**

```javascript
// app.js
const express = require("express");
const app = express();
app.use(express.json());
app.get("/api/items", (req, res) => {
  /* ... */
});
module.exports = app;
```

**Bun:**

```typescript
// server.ts
Bun.serve({
  port: 3000,
  fetch(req) {
    /* ... */
  },
});
```

---

## 1.4 Seed the Vulnerabilities / Scenarios

For a typical 11-18 item rubric, you usually need 4-6 distinct vulnerability classes or scenario axes. Each axis produces 2-4 rubric items. Go above that range only when the extra items come from genuinely different behaviors rather than simple endpoint repetition.

### Security Task Example (task01 pattern)

| Vulnerability Class     | Where to Seed                      | Rubric Items |
| ----------------------- | ---------------------------------- | ------------ |
| Access control (IDOR)   | Read endpoints missing team checks | 3 items      |
| Field redaction         | Admin-only fields not stripped     | 3 items      |
| SQL injection           | Raw string interpolation in search | 1 item       |
| Sensitive data exposure | Debug endpoints with no auth       | 2 items      |
| Mass assignment         | PATCH accepts admin-only fields    | 2 items      |
| Information exposure    | Error handler returns stack traces | 1 item       |
| Regression guards       | Legitimate flows must still work   | 2 items      |
| Test quality            | Sentinel markers in assertions     | 1 item       |

### Feature Task Example

| Scenario Axis     | Where to Seed                   | Rubric Items |
| ----------------- | ------------------------------- | ------------ |
| Happy path        | Core API contract               | 3 items      |
| Error handling    | Invalid inputs, edge conditions | 3 items      |
| Side effects      | DB state, events, downstream    | 2 items      |
| Edge cases        | Boundary values, empty inputs   | 2 items      |
| Regression guards | Existing flows unbroken         | 3 items      |
| Test quality      | Observable behavior assertions  | 2 items      |

---

## 1.5 Code Quality Checklist

Before moving to Step 2, verify:

- [ ] Service is ~300-500 LOC across all source files
- [ ] All bugs/scenarios are deliberately seeded (mark with `# BUG:` comments)
- [ ] In-memory storage with `reset_state()` function
- [ ] Auth module with at least 3 static tokens (admin + 2 users)
- [ ] No external dependencies beyond the framework + test runner
- [ ] Each vulnerability class is exercised by at least one endpoint
- [ ] The service runs locally: `python -m flask --app {substrate}.app run`

---

## Reference: ProjHub (task01) Stats

| Metric                | Value                                                                     |
| --------------------- | ------------------------------------------------------------------------- |
| Total LOC             | ~1,500 (9 route modules)                                                  |
| Endpoints             | 25+                                                                       |
| Vulnerability classes | 6 (IDOR, redaction, SQLi, debug exposure, mass assignment, info exposure) |
| Auth tokens           | 3 (admin, alice/user, bob/user2)                                          |
| In-memory tables      | 5 (teams, projects, tasks, comments, audit_log)                           |
| Requirements          | flask==3.1.0, werkzeug==3.1.3, pytest==8.3.3                              |
