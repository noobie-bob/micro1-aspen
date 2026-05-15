# aspen__projhub_visibility_001

## Tasks in this pack

| Substrate | Rubric Items | Max Score | Status |
|-----------|-------------|-----------|--------|
| projhub (Flask, ~1.5k LOC) | 28 (24 major + 3 minor + 1 nitpick) | 79 | HARDENED — needs re-push + recalibration |

## Substrate Summary

A Flask-based project management API ("ProjHub") with cross-team data isolation failures, injection vulnerabilities, and improper access controls. The service manages teams, projects, tasks, comments, attachments, search, reports, and debug endpoints. Attack surface spans 25+ endpoints across 9 route modules.

**Vulnerability classes:** CWE-284 (Improper Access Control), CWE-639 (IDOR), CWE-200 (Information Disclosure), CWE-862 (Missing Authorization), CWE-89 (SQL Injection), CWE-78 (OS Command Injection), CWE-918 (SSRF), CWE-915 (Mass Assignment), CWE-22 (Path Traversal), CWE-328 (Weak Crypto), CWE-209 (Information Exposure), CWE-1295 (Debug/Deprecated Endpoints)

## Hardening Changes (v4)

- **Source code de-annotated**: All `# BUG:` comments and vulnerability-revealing docstrings stripped from all route modules. Vulnerable code logic is unchanged — bugs must be induced from reading the code, not from labels.
- **Prompt reduced**: `prompt.txt` no longer enumerates vulnerability categories (SQL injection, debug endpoints, mass assignment, etc.). It only hints that "data scoping feels off."
- **Rubric expanded**: 16 → 28 items (44 → 79 points). Added command injection, SSRF, path traversal, weak crypto, admin endpoint access, deprecated APIs, and additional regression guards.
- **Docker image cleaned**: Gold-answer exfiltration tests excluded from container. Only conftest, __init__, and smoke tests are copied.

## Image

- **Tag:** `micro1ai/aspen-projhub:visibility-v4`
- **Digest:** `sha256:ba1a704d7483ac3bb512ecbec2d8658395a775ee4a27041ebadfa5916065434a`
- **Base commit:** _(pending)_
- **Status:** Needs rebuild after hardening changes

## Calibration Results

> **Status:** Pending — recalibration required after hardening.

| Model | N | Mean Reward | Saturation Rate | Pass Rate | Distribution |
|-------|---|-------------|-----------------|-----------|--------------|
| Claude Opus 4.7 | — | — | — | — | — |
| Qwen 3.5 | — | — | — | — | — |

### Per-rubric catch rates (N=12)

| Rubric | Category | Severity | Opus Catch | Qwen Catch |
|--------|----------|----------|------------|------------|
| RUB-001 | access_control | major | — | — |
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
| RUB-012 | sql_injection | major | — | — |
| RUB-013 | command_injection | major | — | — |
| RUB-014 | sensitive_data_exposure | major | — | — |
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
| RUB-027 | input_validation | minor | — | — |
| RUB-028 | test_quality | nitpick | — | — |

### Discrimination ladder rung breakdown

| Rung | Description | Rubric Items |
|------|-------------|--------------|
| Floor | Any model catches basic access control | RUB-001–004 |
| Mid | Model catches redaction + ownership + admin endpoints | RUB-005–011 |
| Ceiling | Model catches injection, SSRF, crypto, sensitive data | RUB-012–021 |
| Top-of-frontier | Model writes regression guards + sentinel markers | RUB-022–028 |

### Discrimination verdict

**Verdict:** PENDING — requires recalibration after hardening.

## Aspen Pipeline Notes

- The Docker image IS the agent's working environment — there is no in-sandbox test verifier.
- The smoke test (`tests/test_smoke.py`) is load-bearing: it teaches the agent the legitimate API surface.
- The conftest (`tests/conftest.py`) provides `two_teams` fixture that sets up alice in team-alpha and bob in team-beta.
- The prompt does NOT enumerate rubric items — the agent must induce what to test from the code.
- **Source code contains NO BUG annotations** — the agent must reason about the code to find vulnerabilities.
- Image built with `--provenance=false --sbom=false` to avoid E2B OCI parsing issues.
