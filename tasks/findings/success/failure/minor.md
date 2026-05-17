# Calibration Success — Hard Rungs / Minor

Rubric items of **minor** severity that were KEPT after calibration. Models are expected to fail these — they are intentional hard rungs providing discrimination signal.

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | Same-boundary action endpoint usability regression guard | Python | Flask | RUB-009 from aspen__test_authoring_projhub_visibility_001 — regression_guard: same-boundary participant must receive 2xx from duplication, share-link generation, and export endpoints | Kept as a hard rung under minimum-item and dual-contract constraints; both models frequently failed to keep all three success-path assertions together |
| 2 | Error-path sanitization for tool failures | Python | FastMCP | RUB-008 from aspen__mcp_server_vuln_002_v4_elite — tool failures must not leak stack traces or filesystem paths in returned content | Type A hard rung — both models failed consistent leak-sanitization coverage |
