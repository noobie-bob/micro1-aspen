# aspen__projhub_visibility_001

## Tasks in this pack

| Substrate | Rubric Items | Max Score | Status |
|-----------|-------------|-----------|--------|
| projhub (Flask, ~1.5k LOC) | 28 (3 critical + 22 major + 2 minor + 1 nitpick) | 86 | HARDENED v5 — needs recalibration |

## Substrate Summary

A Flask-based project management API ("ProjHub") with cross-team data isolation failures, injection vulnerabilities, and improper access controls. The service manages teams, projects, tasks, comments, attachments, search, reports, and debug endpoints. Attack surface spans 25+ endpoints across 9 route modules.

**Vulnerability classes:** CWE-284 (Improper Access Control), CWE-639 (IDOR), CWE-200 (Information Disclosure), CWE-862 (Missing Authorization), CWE-89 (SQL Injection), CWE-78 (OS Command Injection), CWE-918 (SSRF), CWE-915 (Mass Assignment), CWE-22 (Path Traversal), CWE-328 (Weak Crypto), CWE-209 (Information Exposure), CWE-1295 (Debug/Deprecated Endpoints)

## Hardening Changes (v5)

- **Source code de-annotated**: All `# BUG:` comments and vulnerability-revealing docstrings stripped from all route modules. Vulnerable code logic is unchanged — bugs must be induced from reading the code, not from labels.
- **Prompt reduced**: `prompt.txt` no longer enumerates vulnerability categories or references example tests. It only hints that "data scoping feels off" and points the agent to `tests/conftest.py` for fixtures.
- **No tests in image**: Only `conftest.py` ships in the image — the agent writes ALL test files from scratch, including smoke/regression tests.
- **Rubric rebalanced**: 3 critical (×5) + 22 major (×3) + 2 minor (×2) + 1 nitpick (×1) = 86 points. Rubric descriptions are behaviourally abstract — no field names, endpoint paths, or vulnerability mechanisms leaked.
- **Tests consolidated**: Gold test suite reduced from 90 → 28 tests by merging near-duplicate variants (e.g., 3 command injection → 1 loop, 7 mass assignment → 2 multi-field). Each test requires fixing ALL sub-cases to pass.

## Image

- **Tag:** `micro1ai/aspen-projhub:visibility-v5`
- **Digest:** `sha256:6c134d171132ea8eb76134afbe44894b54f32d4b8a16c1ad52f45ad76dd287d8`
- **Base commit:** `1f8214bd4f3654f417a546651f7a21119dd6e29e`
- **Status:** Pushed to Docker Hub — set to PRIVATE

## Calibration Results

> **Status:** Pending — recalibration required after v5 hardening.

| Model | N | Mean Reward | Saturation Rate | Pass Rate | Distribution |
|-------|---|-------------|-----------------|-----------|--------------|
| Claude Opus 4.7 | — | — | — | — | — |
| Qwen 3.5 | — | — | — | — | — |

### Per-rubric catch rates (N=12)

| Rubric | Category | Severity | Opus Catch | Qwen Catch |
|--------|----------|----------|------------|------------|
| RUB-001 | access_control | critical | — | — |
| RUB-002 | access_control | major | — | — |
| RUB-003 | access_control | major | — | — |
| RUB-004 | access_control | major | — | — |
| RUB-005 | ownership | major | — | — |
| RUB-006 | ownership | major | — | — |
| RUB-007 | redaction | major | — | — |
| RUB-008 | redaction | major | — | — |
| RUB-009 | redaction | major | — | — |
| RUB-010 | admin_endpoint | major | — | — |
| RUB-011 | admin_endpoint | major | — | — |
| RUB-012 | sql_injection | critical | — | — |
| RUB-013 | command_injection | major | — | — |
| RUB-014 | sensitive_data_exposure | critical | — | — |
| RUB-015 | sensitive_data_exposure | major | — | — |
| RUB-016 | improper_assets | major | — | — |
| RUB-017 | mass_assignment | major | — | — |
| RUB-018 | mass_assignment | major | — | — |
| RUB-019 | ssrf | major | — | — |
| RUB-020 | information_exposure | major | — | — |
| RUB-021 | weak_crypto | major | — | — |
| RUB-022 | regression_guard | major | — | — |
| RUB-023 | regression_guard | major | — | — |
| RUB-024 | regression_guard | major | — | — |
| RUB-025 | regression_guard | minor | — | — |
| RUB-026 | traversal | minor | — | — |
| RUB-027 | sensitive_data_exposure | major | — | — |
| RUB-028 | test_quality | nitpick | — | — |

### Discrimination ladder rung breakdown

| Rung | Description | Rubric Items |
|------|-------------|--------------|
| Floor | Any model catches basic access control, admin gating | RUB-002–006, RUB-010–011 |
| Mid | Model catches field redaction, same-boundary scoping, deprecated assets | RUB-001, RUB-007–009, RUB-016 |
| Ceiling | Model catches injection, SSRF, crypto, sensitive data, error sanitisation | RUB-012–015, RUB-019–021, RUB-027 |
| Top-of-frontier | Model writes multi-field mass assignment + regression guards with sentinel markers | RUB-017–018, RUB-022–028 |

### Discrimination verdict

**Verdict:** PENDING — requires recalibration after v5 hardening.

## Aspen Pipeline Notes

- The Docker image IS the agent's working environment — there is no in-sandbox test verifier.
- Only `conftest.py` ships in the image — the agent must write all tests from scratch.
- The conftest provides the `two_teams` fixture that sets up alice in team-alpha and bob in team-beta.
- The prompt does NOT enumerate rubric items — the agent must induce what to test from the code.
- **Source code contains NO BUG annotations** — the agent must reason about the code to find vulnerabilities.
- Image built with `--platform linux/amd64 --provenance=false --sbom=false` to avoid E2B OCI parsing issues.
