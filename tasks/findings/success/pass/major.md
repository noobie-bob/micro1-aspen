# Calibration Success — Validated / Major

Rubric items of **major** severity that were KEPT and validated during calibration. Opus passes, Qwen fails — these are the core discrimination signal items.

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | System introspection endpoints — multi-caller access denial | Python | Flask | RUB-015 from aspen__projhub_visibility_001 — sensitive_data_exposure: runtime config and environment endpoints tested against both unauthenticated and non-admin callers | Type B — Opus covered both caller types across both introspection endpoints; Qwen tested only one caller or one endpoint |
| 2 | Regression guard — legitimate network tool usage | Python | FastMCP | RUB-012 from aspen__mcp_server_vuln_002 — regression_guard: legitimate ping_team_server call with a safe target must still succeed after security fixes | Type B — Opus passed; Qwen failed (avg 0%); core discrimination signal |
