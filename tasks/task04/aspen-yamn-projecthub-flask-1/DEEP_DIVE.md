# Deep Dive: ProjectHub Flask Visibility

> **Audience.** A reader who has not seen this repo or the task before. After this file you should be able to say (a) what an AI model is being graded on, (b) what the leak looks like in code, (c) why test-authoring (not a fix) is the right deliverable, and (d) how the rubric maps to realistic threat vectors.

---

## 1. Five-second summary

A frontier model is asked to write a hidden pytest suite for a compact Flask `projhub` service that intentionally exposes privileged fields and widened discovery paths. The agent authors tests that (a) catch the leak across primary and auxiliary surfaces and (b) assert anti-overblock regression guards so legitimate admin and same-team flows remain functional.

## 2. Why test-authoring is the right shape

- The fix shape is ambiguous in real products (redaction, gate hardening, or storage change). Grading fixes conflates taste with threat understanding.
- A test suite is unambiguous: it encodes the threat model and ensures a correct fix closes the leak while preserving legitimate flows (the dual contract).

## 3. The setup — what the agent sees

The agent runs in the task image with the following entrypoints:

- `projhub/app.py` — route registration, gates, serializers, and seeded insecure surfaces.
- `projhub/db.py` — in-memory seed data and sentinel markers.
- `tests/test_smoke.py` — legitimate participant and admin flows (naturalistic guidance; do not change).

Seeded actors: `admin` (`admin-key`), `participant` (`user-key`), `participant` 2 (`user2-key`), and a `lead` (`lead-key`). The prompt forbids any source changes under `projhub/`.

## 4. Key endpoints and leak shapes

| Endpoint | Intended use | Bug / leak shape |
|---|---|---|
| `GET /projects/<id>` | Primary project read | Returns privileged admin fields in some response shapes (response-shaping leak)
| `GET /projects` | Project listing/discovery | Intentional widened discovery (`include=all`, `q` variants) exposes extra rows
| `GET /projects/<id>/export` | Export/package | Team export may return full project object (metadata leak)
| `POST /projects/<id>/share` | Package share payload | Inlines `admin_config` and `internal_metrics` in share payload
| `POST /projects/<id>/duplicate` | Duplicate/fork | Duplicate may copy privileged fields into the clone (laundering)
| `GET /tasks/<id>` | Task read | Task view sometimes includes privileged reviewer/internal fields
| `GET /tasks/<id>/comments` | Comments list | Intentional pinned/internal leak exposes internal comments to non-admins
| `GET /tasks/<id>/attachments/<path>` | Attachment fetch | Traversal-style leak returns `KV.root_file` for `..` or absolute paths
| `GET /search/projects`, `GET /search/tasks` | Search surfaces | Crafted queries (`or`, `union`, `--`) or `debug=1` reveal admin fields
| `POST /projects/<id>/generate-report` | Formatter/generator | Crafted `title` or `format` with shell-like chars returns `stdout` echo (command-output leak)
| `POST /tasks/<id>/notify-webhook` | Webhook enqueue | Accepts non-validated URL and echoes target host (SSRF-like information leak)
| `/debug/*`, `/ops/*` | Debug/operational | Debug dump and ops cursors return internal state, team tables, and KV data

These shapes provide multiple exfiltration vectors without modifying the codebase.

## 5. The rubric — what counts as a good test suite

The `ground_truth_issues[]` in `task_config.json` decomposes the threat model into behavioural items. High-level groups:

- Read-side cross-boundary coverage (critical): assert non-privileged callers cannot see seeded cross-boundary project/task markers in direct readbacks and discovery/search paths.
- Response-shaping and packaging (critical): assert exports, shares, and duplicate/package flows do not leak admin-only metadata to ordinary participants.
- Delegated-share and token properties (major): verify shares are scoped, accepted, and expire correctly; tokens are non-predictable or correctly validated.
- Internal/comment/attachment hygiene (major): pinned/internal comments and attachments must not leak privileged content to ordinary callers; traversal is contained.
- Anti-overblock regression guards (major/minor): assert admin visibility and same-team positive flows remain intact after fixes (dual contract).
- Test quality & repeatability (minor): tests must use sentinel markers and isolate state for repeatability.

Each rubric item is weighted (critical=4, major=3, minor=2, nitpick=1). The task's severity arithmetic totals to 41 (4×4 + 7×3 + 2×2).

## 6. Why this is realistic

- Multi-surface leaks (discovery, export, debug, search) are common in real systems when serializers and gate checks drift apart.
- Duplicate/fork laundering chains are realistic for systems that deep-copy rows; they produce subtle write-side privacy regressions.
- Debug/ops endpoints and naive formatter or shell-like handling are frequent accidental exposure sources.

## 7. How calibration runs work

This task is `pipeline: aspen` with `rubric_only: true`. The platform generates one NL-assertion per `ground_truth_issues[]` entry and the LLM judge scores the agent's git diff against each assertion, weighted by severity.

Calibration practice: start with a small frontier triad, escalate per-model sampling for variance, and inspect per-rubric catch rates to confirm discrimination.

## 8. What to run locally (developer notes)

Run the smoke tests to verify the image and fixtures:

```bash
python -m pytest tests/test_smoke.py -q
```

Gold-standard exfiltration tests should be placed in `tests/exfiltration/` and asserted via sentinel markers and body-level checks.

