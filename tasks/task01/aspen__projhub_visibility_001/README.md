# aspen__projhub_visibility_001

## Tasks in this pack

| Substrate | Rubric Items | Max Score | Status |
|-----------|-------------|-----------|--------|
| projhub (Flask, ~1.5k LOC) | 16 (13 major + 2 minor + 1 nitpick) | 44 | PUSHED — awaiting calibration |

## Substrate Summary

A Flask-based project management API ("ProjHub") with cross-team data isolation failures, injection vulnerabilities, and improper access controls. The service manages teams, projects, tasks, comments, attachments, search, reports, and debug endpoints. Attack surface spans 25+ endpoints across 9 route modules.

**Vulnerability classes:** CWE-284 (Improper Access Control), CWE-639 (IDOR), CWE-200 (Information Disclosure), CWE-862 (Missing Authorization), CWE-89 (SQL Injection), CWE-78 (OS Command Injection), CWE-918 (SSRF), CWE-915 (Mass Assignment), CWE-22 (Path Traversal), CWE-328 (Weak Crypto), CWE-209 (Information Exposure), CWE-1295 (Debug/Deprecated Endpoints)

## Image

- **Tag:** `micro1ai/aspen-projhub:visibility-v2`
- **Digest:** `sha256:5e8f8849a569d29ecb33adf677a59f93555083bfde2a09e266b5c979993a3620`
- **Base commit:** `0124c1e9beb295c90bd57e2321d81068c4fa2b5e`
- **Status:** Pushed to Docker Hub — set to PRIVATE

## Calibration Results

> **Status:** Pending — calibration runs have not been executed yet.
> Run N=12 per model, then fill in the tables below.

| Model | N | Mean Reward | Saturation Rate | Pass Rate | Distribution |
|-------|---|-------------|-----------------|-----------|--------------|
| Claude Opus 4.7 | — | — | — | — | — |
| Qwen 3.5 | — | — | — | — | — |

### Gemini N=10 stability — pass@k

> Fill after running Gemini stability checks.

| Threshold | pass@1 | pass@3 | pass@5 | pass@10 |
|-----------|--------|--------|--------|---------|
| reward ≥ 0.5 | — | — | — | — |
| reward ≥ 0.8 | — | — | — | — |

### Per-rubric catch rates (N=12)

| Rubric | Category | Severity | Opus Catch | Qwen Catch |
|--------|----------|----------|------------|------------|
| RUB-001 | access_control | major | — | — |
| RUB-002 | access_control | major | — | — |
| RUB-003 | access_control | major | — | — |
| RUB-004 | redaction | major | — | — |
| RUB-005 | redaction | major | — | — |
| RUB-006 | redaction | major | — | — |
| RUB-007 | sql_injection | major | — | — |
| RUB-008 | sensitive_data_exposure | major | — | — |
| RUB-009 | sensitive_data_exposure | major | — | — |
| RUB-010 | mass_assignment | major | — | — |
| RUB-011 | mass_assignment | major | — | — |
| RUB-012 | information_exposure | major | — | — |
| RUB-013 | regression_guard | major | — | — |
| RUB-014 | regression_guard | minor | — | — |
| RUB-015 | input_validation | minor | — | — |
| RUB-016 | test_quality | nitpick | — | — |

### Discrimination ladder rung breakdown

| Rung | Description | Rubric Items |
|------|-------------|--------------|
| Floor | Any model catches basic access control | RUB-001–003 |
| Mid | Model catches redaction + injection bugs | RUB-004–007 |
| Ceiling | Model catches sensitive data, mass assignment, info exposure | RUB-008–012 |
| Top-of-frontier | Model writes regression guards + sentinel markers | RUB-013–016 |

### Discrimination verdict

**Verdict:** PENDING — requires calibration runs.

> After calibration, set to one of: `DISCRIMINATIVE` / `UNDER-CALIBRATED` / `FLAKY`
> with rationale based on Opus vs Qwen separation.

## Aspen Pipeline Notes

- The Docker image IS the agent's working environment — there is no in-sandbox test verifier.
- The smoke test (`tests/test_smoke.py`) is load-bearing: it teaches the agent the legitimate API surface.
- The conftest (`tests/conftest.py`) provides `two_teams` fixture that sets up alice in team-alpha and bob in team-beta.
- The prompt does NOT enumerate rubric items — the agent must induce what to test from the code.
- 23 smoke tests pass in the container (verified).
- Image built with `--provenance=false --sbom=false` to avoid E2B OCI parsing issues.
