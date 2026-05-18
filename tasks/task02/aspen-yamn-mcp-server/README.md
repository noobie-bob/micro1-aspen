# aspen__mcp_server_vuln_002

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
| RUB-002 | code_injection | critical | — | — |
| RUB-003 | credentials_multi_caller_content_check | critical | — | — |
| RUB-004 | untrusted_module_loading | major | — | — |
| RUB-005 | regression_legitimate_flows | major | — | — |
| RUB-006 | ssrf_internal_target_nonfetch | critical | — | — |
| RUB-007 | safe_module_loading_with_controls | critical | — | — |
| RUB-008 | regression_same_team_lifecycle | major | — | — |
| RUB-009 | eval_result_field_clean_with_arithmetic_control | critical | — | — |
| RUB-010 | fetch_asset_internal_address_variants_all_blocked | critical | — | — |
| RUB-011 | legacy_diagnostic_multi_caller_content_denial | critical | — | — |
| RUB-012 | ping_injection_multi_payload_sweep | critical | — | — |
| RUB-013 | cross_team_search_isolation_content_proof | critical | — | — |
| RUB-014 | delete_verify_dual_surface_chain | major | — | — |

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
