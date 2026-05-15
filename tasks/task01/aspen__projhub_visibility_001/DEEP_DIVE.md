# Deep Dive: ProjHub Cross-Team Visibility Task

## Five-Second Summary

ProjHub is a Flask project-management API with **25+ endpoints** managing teams, projects, tasks, comments, and attachments. The service has seeded vulnerabilities spanning 12 OWASP classes — from basic IDOR and missing access control to SQL injection, OS command injection, SSRF, mass assignment, weak cryptography, path traversal, and sensitive data exposure via debug endpoints. The agent must author a test suite that catches all of these without over-blocking legitimate flows.

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
│       ├── search.py           # SQLite search + share-link
│       ├── reports.py          # Report generation, webhooks, export-file
│       └── debug.py            # Debug/diagnostic + legacy API endpoints
├── tests/
│   ├── conftest.py             # Fixtures: client, auth headers, two_teams
│   └── test_smoke.py           # 23 load-bearing legitimate-flow tests
├── requirements.txt
└── pytest.ini
```

The agent reads `prompt.txt` (which mentions access boundary concerns but does NOT enumerate specific vulnerability types or rubric items), then must explore the codebase to find all vulnerability surfaces.

**Important:** The source code contains NO `# BUG:` annotations or vulnerability labels. The agent must reason about the code to discover issues.

### Auth Model

| Token | Role | User ID | Team |
|-------|------|---------|------|
| `admin-key` | admin | admin-uuid | org-wide |
| `user-key` | user | alice-uuid | team-alpha (via fixture) |
| `user2-key` | user | bob-uuid | team-beta (via fixture) |

## How the Rubric Decomposes the Scenario

| Category | Items | What It Tests |
|----------|-------|---------------|
| access_control (4) | RUB-001–004 | Cross-team read isolation on list/detail/task endpoints |
| ownership (2) | RUB-005–006 | Cross-team PATCH/DELETE prevention |
| redaction (3) | RUB-007–009 | Admin-only field stripping from responses |
| admin_endpoint (2) | RUB-010–011 | Admin endpoint access control |
| sql_injection (1) | RUB-012 | Search endpoint parameterization |
| command_injection (1) | RUB-013 | Report generation shell injection |
| sensitive_data_exposure (2) | RUB-014–015 | Debug endpoints removed or auth-gated |
| improper_assets (1) | RUB-016 | Deprecated v1 API access control |
| mass_assignment (2) | RUB-017–018 | PATCH rejects admin-only fields from non-admin |
| ssrf (1) | RUB-019 | Webhook URL validation |
| information_exposure (1) | RUB-020 | Error responses don't leak stack traces |
| weak_crypto (1) | RUB-021 | Share-link token unpredictability |
| regression_guard (4) | RUB-022–025 | Anti-overblock: admin, same-team, create, dup/share/export |
| traversal (1) | RUB-026 | Path traversal in attachment download |
| input_validation (1) | RUB-027 | Database dump endpoint access control |
| test_quality (1) | RUB-028 | Sentinel marker assertions |

**Total: 28 items.** 24 major (×3) + 3 minor (×2) + 1 nitpick (×1) = **79 points.** rubric_max_score = 79.

## How to Read the Calibration Numbers

Once calibration is run (N=12 per model):

- **Mean Reward** — Average rubric score as fraction of max (79). Higher = model catches more bugs.
- **Saturation Rate** — Fraction of runs that score ≥ 80% of max. Measures consistency.
- **Pass Rate** — Fraction of runs where smoke tests still pass after adding exfiltration tests.
- **Catch Rate per rubric** — How often each rubric item is caught across N runs. Items caught by all models are "floor" items; items caught only by frontier models are discriminative.

**Discrimination ladder:**
- **Floor** (any model catches): basic IDOR/access control (RUB-001–004)
- **Mid** (strong models catch): ownership, redaction, admin endpoints (RUB-005–011)
- **Ceiling** (frontier-only): injection, SSRF, crypto, sensitive data, deprecated APIs (RUB-012–021)
- **Top-of-frontier**: regression guards + sentinel markers (RUB-022–028)

A task is **DISCRIMINATIVE** if there's clear separation between frontier and non-frontier model scores. It's **UNDER-CALIBRATED** if all models score similarly, and **FLAKY** if scores vary wildly within the same model.
