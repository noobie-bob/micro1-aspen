# Deep Dive: ProjHub Cross-Team Visibility Task

## Five-Second Summary

ProjHub is a Flask project-management API with **25+ endpoints** managing teams, projects, tasks, comments, and attachments. The service has seeded vulnerabilities spanning 11 OWASP classes — from basic IDOR and missing access control to SQL injection, OS command injection, SSRF, mass assignment, and sensitive data exposure via debug endpoints. The agent must author a test suite that catches all of these without over-blocking legitimate flows.

## Why Test-Authoring Is the Right Shape

The **dual-contract argument**: a secure project-management API must enforce two invariants simultaneously:

1. **Isolation contract** — Users must only see/modify resources belonging to their team. Admin-only fields must be redacted. Injection endpoints must be hardened.
2. **Usability contract** — Legitimate same-team operations, admin workflows, and public endpoints must continue working after any fix.

A bug-fix task would let the agent patch one or two endpoints and call it done. A test-authoring task forces the agent to **induce the full threat model from the code** — every endpoint, every field, every access-control gap — and encode both the isolation and usability contracts as executable assertions. This is strictly harder and more discriminative.

## What the Agent Sees

The agent lands in `/repo` with:

```
/repo/
├── projhub/                    # The Flask service (DO NOT MODIFY)
│   ├── app.py                  # App factory, error handlers
│   ├── auth.py                 # Bearer token auth (admin, alice, bob)
│   ├── db.py                   # In-memory storage
│   └── routes/
│       ├── teams.py            # Team CRUD
│       ├── projects.py         # Project CRUD + duplicate/share/export
│       ├── tasks.py            # Task CRUD + assign/transition
│       ├── comments.py         # Comment CRUD
│       ├── attachments.py      # Upload/download
│       ├── admin.py            # Audit log, reports
│       ├── search.py           # SQLite search
│       ├── reports.py          # Report generation, webhooks
│       └── debug.py            # Debug/deprecated endpoints
├── tests/
│   ├── conftest.py             # Fixtures: client, auth headers, two_teams
│   └── test_smoke.py           # 23 load-bearing legitimate-flow tests
├── requirements.txt
└── pytest.ini
```

The agent reads `prompt.txt` (which mentions cross-team leaks and "something weird with the SQL" but does NOT enumerate rubric items), then must explore the codebase to find all vulnerability surfaces.

### Auth Model

| Token | Role | User ID | Team |
|-------|------|---------|------|
| `admin-key` | admin | admin-uuid | org-wide |
| `user-key` | user | alice-uuid | team-alpha (via fixture) |
| `user2-key` | user | bob-uuid | team-beta (via fixture) |

### Key Code Patterns to Notice

**Access control gaps** — Most endpoints use `@require_auth` (any authenticated user) instead of checking team membership:
```python
# routes/projects.py — BUG: returns ALL projects from all teams
@bp.route("/projects", methods=["GET"])
@require_auth
def list_projects():
    return jsonify(list(PROJECTS.values()))
```

**Mass assignment** — PATCH handlers accept admin-only fields:
```python
# routes/tasks.py — BUG: non-admin can set internal_priority
for key in ("title", "description", "status", "priority", "assigned_to",
            "internal_priority", "reviewer_notes",
            "security_classification", "estimated_cost"):
```

**SQL injection** — Search uses raw string interpolation:
```python
# routes/search.py — BUG: f-string SQL
sql = f"SELECT ... FROM task_index WHERE title LIKE '%{q}%'"
```

**OS command injection** — Report generation uses `shell=True`:
```python
# routes/reports.py — BUG: unsanitised input in shell command
cmd = f"echo 'Report: {title}' | head -c 1024"
result = subprocess.run(cmd, shell=True, ...)
```

**Debug endpoints** — No auth required, leak everything:
```python
# routes/debug.py — BUG: leaks all API tokens
@bp.route("/debug/users", methods=["GET"])
def debug_users():
    # returns plaintext tokens for all users including admin
```

## How the Rubric Decomposes the Scenario

| Category | Items | What It Tests |
|----------|-------|---------------|
| access_control (3) | RUB-001–003 | Cross-team read isolation on list/detail endpoints |
| redaction (3) | RUB-004–006 | Admin-only field stripping from responses |
| sql_injection (1) | RUB-007 | Search endpoint parameterisation |
| sensitive_data_exposure (2) | RUB-008–009 | Debug endpoints removed or auth-gated |
| mass_assignment (2) | RUB-010–011 | PATCH rejects admin-only fields from non-admin |
| information_exposure (1) | RUB-012 | Error responses don't leak stack traces |
| regression_guard (2) | RUB-013–014 | Anti-overblock: same-team works, duplicate/share/export |
| input_validation (1) | RUB-015 | Database dump endpoint access control |
| test_quality (1) | RUB-016 | Sentinel marker assertions |

**Total: 16 items.** 13 major (×3) + 2 minor (×2) + 1 nitpick (×1) = **44 points max.**

## How to Read the Calibration Numbers

Once calibration is run (N=12 per model):

- **Mean Reward** — Average rubric score as fraction of max (44). Higher = model catches more bugs.
- **Saturation Rate** — Fraction of runs that score ≥ 80% of max. Measures consistency.
- **Pass Rate** — Fraction of runs where smoke tests still pass after adding exfiltration tests.
- **Catch Rate per rubric** — How often each rubric item is caught across N runs. Items caught by all models are "floor" items; items caught only by frontier models are discriminative.

**Discrimination ladder:**
- **Floor** (any model catches): basic IDOR/access control (RUB-001–003)
- **Mid** (strong models catch): redaction + injection (RUB-004–007)
- **Ceiling** (frontier-only): sensitive data, mass assignment, info exposure (RUB-008–012)
- **Top-of-frontier**: regression guards + sentinel markers (RUB-013–016)

A task is **DISCRIMINATIVE** if there's clear separation between frontier and non-frontier model scores. It's **UNDER-CALIBRATED** if all models score similarly, and **FLAKY** if scores vary wildly within the same model.

