# Calibration Success — Validated / Minor

Rubric items of **minor** severity that were KEPT and validated during calibration. Opus passes, Qwen fails — these are the core discrimination signal items.

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | Same-boundary action endpoint regression guard | Python | Flask | RUB-025 from aspen__projhub_visibility_001 — regression_guard: duplication, sharing, and export action endpoints must all succeed for a same-boundary participant | Type B — Opus covered all three action endpoints in the regression path; Qwen missed one or more action types |
| 2 | Stack trace and filesystem path absence from tool error responses | Python | FastMCP | RUB-008 from aspen__mcp_server_vuln_002_v4_elite — traceback_leak: no tool should return Python stack traces or internal filesystem paths in error responses; assertion is content-level absence check | Type B — Opus passed; Qwen avg 14%; content-level path/traceback absence check is the rung Qwen missed |
