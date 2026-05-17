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
│   └── conftest.py             # Fixtures: client, auth headers, two_teams
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
| ownership (1) | RUB-001 | major | Cross-boundary destructive operations with state-preservation readback |
| redaction (2) | RUB-002, RUB-011 | major | Privileged field suppression in detail or derived responses and internal-only discussion filtering with a visible public-control comment |
| admin_endpoint (2) | RUB-003, RUB-010 | major | Operator activity and management surfaces denied to lower-privilege callers while admin access stays usable |
| sensitive_data_exposure (6) | RUB-004, RUB-009, RUB-015, RUB-017, RUB-018, RUB-019 | major | Credential-oriented and runtime-diagnostic surfaces denied across caller classes with content-level non-leak checks across multiple diagnostic paths |
| regression_guard (8) | RUB-005–008, RUB-012–014, RUB-016 | major / minor | Admin full-visibility plus same-boundary read, write, action-path usability, and admin-positive-control diagnostics |

**Total: 19 items.** 18 major (×3) + 1 minor (×2) = **56 points.** rubric_max_score = 56.

## How to Read the Calibration Numbers

The most recent measured state on the pre-trim 18-item rubric reached Opus `63.8%`, Qwen `38.2%`, spread `25.6%`. The safe trim set improved the trim-only ceiling but still did not clear Opus. This revision therefore keeps the safe trim, preserves the denser Type B-style rewrites, and adds three more near-neighbor diagnostic-denial items, which now requires a full rerun.

For the updated 19-item rubric, read calibration the usual Aspen way:

- **Mean Reward** — Weighted score as a fraction of `56`.
- **Catch Rate per rubric** — Which items models actually satisfy; the new intended Type B items should raise Opus without lifting Qwen equally.
- **Spread** — The meaningful target is still `>= 0.20` between frontier and mid-tier means.

A task is **DISCRIMINATIVE** only after the new 19-item rubric is rerun and shows Opus clearly outscoring Qwen inside the Aspen target bands.
