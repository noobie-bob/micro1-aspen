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

| Category | Items | Severity | What It Tests |
|----------|-------|----------|---------------|
| access_control (4) | RUB-001–004 | critical / major | Cross-boundary read isolation: list scoping, direct ID access, child resource listing, leaf detail |
| ownership (2) | RUB-005–006 | major | Cross-boundary write/delete prevention |
| redaction (3) | RUB-007–009 | major | Privileged field suppression; secondary channel (clone/share/export) redaction with sentinel markers |
| admin_endpoint (2) | RUB-010–011 | major | Administrative endpoint access control |
| sql_injection (1) | RUB-012 | critical | Search endpoint injection: extracting privileged columns via query manipulation |
| command_injection (1) | RUB-013 | major | Report generation shell injection via multiple metacharacter classes |
| sensitive_data_exposure (3) | RUB-014–015, RUB-027 | critical / major | Credential-exposing debug endpoints; config/env endpoints; database dump endpoint |
| improper_assets (1) | RUB-016 | major | Deprecated v1 API access control for both endpoints and both caller types |
| mass_assignment (2) | RUB-017–018 | major | Multi-field PATCH must reject all privileged fields simultaneously |
| ssrf (1) | RUB-019 | major | Webhook URL validation across three private address classes |
| information_exposure (1) | RUB-020 | major | Error responses must suppress stack traces, file paths, and runtime version strings |
| weak_crypto (1) | RUB-021 | major | Share-link token must not be derivable via any common deterministic algorithm |
| regression_guard (4) | RUB-022–025 | major / minor | Anti-overblock: admin full-visibility, same-boundary reads, writes, and action endpoints |
| traversal (1) | RUB-026 | minor | Path traversal blocked across classic, URL-encoded, and cross-resource vectors |
| test_quality (1) | RUB-028 | nitpick | Sentinel marker content-level assertions in addition to status-code checks |

**Total: 28 items.** 3 critical (×5) + 22 major (×3) + 2 minor (×2) + 1 nitpick (×1) = **86 points.** rubric_max_score = 86.

## How to Read the Calibration Numbers

Once calibration is run (N=12 per model):

- **Mean Reward** — Average rubric score as fraction of max (79). Higher = model catches more bugs.
- **Saturation Rate** — Fraction of runs that score ≥ 80% of max. Measures consistency.
- **Pass Rate** — Fraction of runs where smoke tests still pass after adding exfiltration tests.
- **Catch Rate per rubric** — How often each rubric item is caught across N runs. Items caught by all models are "floor" items; items caught only by frontier models are discriminative.

**Discrimination ladder:**
- **Floor** (any model catches): basic access control, admin endpoint gating (RUB-002–006, RUB-010–011)
- **Mid** (strong models catch): field redaction, same-boundary scoping, deprecated assets (RUB-001, RUB-007–009, RUB-016)
- **Ceiling** (frontier-only): injection classes, SSRF, crypto, sensitive data exposure, error sanitisation (RUB-012–015, RUB-019–021, RUB-027)
- **Top-of-frontier**: multi-field mass assignment, regression guards with sentinel markers (RUB-017–018, RUB-022–028)

A task is **DISCRIMINATIVE** if there's clear separation between frontier and non-frontier model scores. It's **UNDER-CALIBRATED** if all models score similarly, and **FLAKY** if scores vary wildly within the same model.
