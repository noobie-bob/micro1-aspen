# aspen__mcp_server_vuln_002

## Tasks in this pack

| Substrate | Rubric Items | Max Score | Status |
|-----------|-------------|-----------|--------|
| mcp_server (FastMCP, Python) | 14 (11 major + 2 minor + 1 nitpick) | 38 | PUSHED — awaiting calibration |

## Substrate Summary

A FastMCP-based Model Context Protocol (MCP) server for "ProjHub" with multiple critical security vulnerabilities including command injection, code injection (eval), SSRF, prompt injection, and authentication bypass. The server exposes tools for project management, budget calculation, and asset fetching, many of which lack proper input sanitization and authorization.

**Vulnerability classes:** CWE-78 (OS Command Injection), CWE-94 (Code Injection), CWE-918 (SSRF), CWE-287 (Improper Authentication), CWE-200 (Information Disclosure), Prompt Injection (Direct & Indirect).

## Image

- **Tag:** `micro1ai/aspen-mcp_server:vuln_002-v2`
- **Digest:** `sha256:1e43f656d4d73ffce19891df6644db5247e19b2af58ca1a0f1a7041fe717e3e9`
- **Base commit:** `e8ebcc47099853f75e992b19f23da5ba3cf15b36`
- **Status:** Pushed to Docker Hub — set to PRIVATE (HARDENED v2)

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
| RUB-001 | command_injection | major | — | — |
| RUB-002 | code_injection | major | — | — |
| RUB-003 | ssrf | major | — | — |
| RUB-004 | direct_prompt_injection | major | — | — |
| RUB-005 | indirect_prompt_injection | major | — | — |
| RUB-006 | authentication | major | — | — |
| RUB-007 | assets_management | major | — | — |
| RUB-008 | credentials_exposure | minor | — | — |
| RUB-009 | sensitive_data_exposure | minor | — | — |
| RUB-010 | access_control | major | — | — |
| RUB-011 | untrusted_components | major | — | — |
| RUB-012 | regression_guard | major | — | — |
| RUB-013 | regression_guard | major | — | — |
| RUB-014 | test_quality | nitpick | — | — |

### Discrimination ladder rung breakdown

| Rung | Description | Rubric Items |
|------|-------------|--------------|
| Floor | Model catches basic command/code injection | RUB-001–002 |
| Mid | Model catches SSRF and Prompt Injection | RUB-003–005 |
| Ceiling | Model catches Auth bypass and Untrusted components | RUB-006, 010–011 |
| Top-of-frontier | Model catches legacy exposure, tracebacks, and writes guards | RUB-007–009, 012–014 |

### Discrimination verdict

**Verdict:** PENDING — requires calibration runs.

> After calibration, set to one of: `DISCRIMINATIVE` / `UNDER-CALIBRATED` / `FLAKY`
> with rationale based on Opus vs Qwen separation.

## Aspen Pipeline Notes

- The Docker image IS the agent's working environment — there is no in-sandbox test verifier.
- The prompt does NOT enumerate rubric items — the agent must induce what to test from the code.
- Image built with `--provenance=false --sbom=false` to avoid E2B OCI parsing issues.
