---
name: aspen-step1
description: "Step 1 walkthrough: design and build the substrate service. Service type selection (Flask/FastAPI/Go/Node/Bun), naming convention (aspen__{substrate}_{class}_{NNN}), directory scaffolding, implementing ~300-500 LOC service with in-memory storage, seeding vulnerabilities/scenarios across 4-6 axes. Load when starting Step 1 of a new task."
user-invocable: false
---

# Step 1: Design & Build the Substrate Service

> **Goal:** Choose your service type, define the scenario, and implement the hand-authored codebase (~300-500 LOC) the AI agent will review.

## 1.1 Choose Your Service & Scenario

| Stack | Framework | When to Use |
|---|---|---|
| Python + Flask | `flask==3.1.0` | Security vulns, API testing, rapid prototyping |
| Python + FastAPI | `fastapi`, `uvicorn` | Async APIs, type-checked routes |
| Go | `net/http`, `chi`, `gin` | Systems-level bugs, concurrency issues |
| Node.js + Express | `express` | JS ecosystem, middleware bugs |
| Node.js + Bun | `bun serve` | Fast runtime, JS/TS edge cases |

| Scenario Type | Example | Categories |
|---|---|---|
| Security (IDOR/access control) | Cross-team data isolation failure | `access_control`, `ownership`, `redaction` |
| Security (injection) | SQL injection, command injection | `sql_injection`, `command_injection` |
| Feature coverage | New payment API contract | `happy_path`, `error_handling`, `edge_case` |
| Regression guard | Date parsing bug in timezone conversion | `bug_reproduction`, `related_path` |
| Edge case | Race condition in concurrent writes | `concurrency`, `data_integrity` |

### Naming Convention

```
aspen__{substrate}_{vulnerability_class}_{NNN}
```

Examples:
- `aspen__projhub_visibility_001` — Flask project management, visibility vulns
- `aspen__billing_sqli_001` — Billing API, SQL injection
- `aspen__filestore_traversal_001` — File store, path traversal

## 1.2 Scaffold the Directory Structure

```
micro1-aspen/tasks/task{NN}/
├── .dockerignore
├── Dockerfile                       # Local testing image
├── requirements.txt
├── pytest.ini
├── {substrate}/
│   ├── __init__.py
│   ├── app.py
│   ├── auth.py
│   ├── db.py
│   └── routes/
│       ├── __init__.py
│       ├── feature_a.py
│       ├── feature_b.py
│       └── debug.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_smoke.py
└── aspen__{substrate}_{vuln}_{NNN}/
    ├── prompt.txt
    ├── task_config.json
    ├── reasoning.txt
    ├── README.md
    ├── DEEP_DIVE.md
    └── Dockerfile                   # Production image
```

## 1.3 Implement the Service (~300-500 LOC)

### Key Principles

1. **Seed the bugs intentionally** — Every vulnerability/scenario must be deliberate and precisely scoped
2. **Keep it self-contained** — In-memory storage, no external database dependencies
3. **Use realistic patterns** — The code should look like real production code that has bugs, not toy code

### Flask Service Pattern (from task01)

**`app.py`** — App factory:
```python
from flask import Flask, jsonify
from {substrate}.db import reset_state
from {substrate}.routes import feature_a, feature_b, debug

def create_app() -> Flask:
    reset_state()
    app = Flask(__name__)
    app.register_blueprint(feature_a.bp)
    app.register_blueprint(feature_b.bp)
    app.register_blueprint(debug.bp)
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

def reset_state() -> None:
    """Wipe all storage. Called at app startup and from tests."""
    TEAMS.clear()
    PROJECTS.clear()
```

## 1.4 Seed the Vulnerabilities / Scenarios

For a typical 11-18 item rubric, you usually need 4-6 distinct vulnerability classes or scenario axes. Each axis produces 2-4 rubric items.

| Vulnerability Class | Where to Seed | Rubric Items |
|---|---|---|
| Access control (IDOR) | Read endpoints missing team checks | 3 items |
| Field redaction | Admin-only fields not stripped | 3 items |
| SQL injection | Raw string interpolation in search | 1 item |
| Sensitive data exposure | Debug endpoints with no auth | 2 items |

### Critical Rules for Seeding

- **Do NOT comment the bug** — No `# BUG:`, `# VULNERABILITY:`, or revealing docstrings
- **Do NOT make it obvious** — The code should look like it could be intentional or a simple oversight
- **De-annotate before shipping** — Remove any internal markers before building the Docker image
- **Each axis must be testable** — The agent must be able to discover and test each vulnerability from the running service
