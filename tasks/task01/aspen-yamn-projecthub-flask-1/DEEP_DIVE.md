# Deep Dive: ProjHub Cross-Team Visibility Task

## Five-Second Summary

ProjHub is a Flask project-management API with **25+ endpoints** managing teams, projects, tasks, comments, and attachments. The trimmed rubric now concentrates on cross-boundary data visibility, privileged metadata leakage, operator diagnostics, and the legitimate same-boundary or admin flows that must keep working after a fix. The agent must author a test suite that catches those failures without over-blocking ordinary usage.

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
| redaction (1) | RUB-001 | major | Privileged field suppression in detail and derived responses with an admin positive control |
| sensitive_data_exposure (3) | RUB-006, RUB-011, RUB-012 | major | GET /debug/users exposes api_token to unauthenticated callers; seeded sentinel absent from /debug/env and /debug/config for lower-privilege callers; both debug endpoints reachable (HTTP 200) without any auth |
| regression_guard (8) | RUB-002–005, RUB-007–010 | major / minor | Admin cross-boundary project listing; participant same-team ID traversal; authenticated project list (GET /projects → 200); POST /projects/{id}/share returns share_id + url; GET /debug/config admin read → python_version present; task create + list read-back; admin team create + GET /teams with admin_notes; participant task create + cross-boundary denial |

**Total: 12 items.** 11 major (×3) + 1 minor (×2) = **35 points.** rubric_max_score = 35.

## How to Read the Calibration Numbers

Five multi-step regression guards that were causing consistent model failure were replaced with simpler single- or two-call tests after calibration analysis. The two harder items (RUB-008, RUB-011) are retained as separation rungs — they require chained create-then-read-back-then-deny flows or seeded-marker absence checks that mid-tier models miss.

- **Mean Reward** — Weighted score as a fraction of `35`.
- **Target composition** — 10 floor items both models pass (Type D) + 2 separation items only the frontier model passes (Type B).
- **Spread** — Meaningful target is `>= 0.20` between frontier and mid-tier means.
