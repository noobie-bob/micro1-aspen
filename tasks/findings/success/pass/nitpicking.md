# Calibration Success — Validated / Nitpick

Rubric items of **nitpick** severity that were KEPT and validated during calibration. Opus passes, Qwen fails — these are the core discrimination signal items.

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | Strict assertions over exception-only tests | Python | FastMCP | RUB-014 from aspen__mcp_server_vuln_002 — test_quality: tests must use explicit state-based assertions rather than relying solely on raised exceptions | Type B — Opus passed; Qwen failed (avg 0%); core discrimination signal |
