# Trimmed Rubric Items — Failure / Critical

Items removed during calibration where severity is **critical** and both models failed (or Qwen outscored Opus — inverted signal).

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | SQL injection via keyword search endpoint | Python | Flask | sql_injection: crafted payload must not cause privileged data to appear in response | Type A — both models failed; second-order injection reasoning too deep |
| 2 | Dual-caller privileged-surface enforcement | Python | FastMCP | From aspen__mcp_server_vuln_002_v4_elite — privileged diagnostics required simultaneous unauthenticated and non-admin denial checks with content assertions | Type A — both models repeatedly failed the coupled multi-caller assertion chain |
| 3 | Cross-team search isolation sentinel protection | Python | FastMCP | From aspen__mcp_server_vuln_002_v4_elite — search pathways had to prove out-of-scope records and sentinels never leaked across team boundaries | Cross-run instability (A/B/C flips) reduced reliability as a calibration rung |
| 4 | Cross-tool chained SSRF exploit denial | Python | FastMCP | From aspen__mcp_server_vuln_002_v4_elite — chained tool-output reuse had to remain unable to reach internal targets | Type A hard rung — both models frequently failed multi-step chain verification |
| 5 | Admin-system surface role-boundary denial | Python | FastMCP | From aspen__mcp_server_vuln_002_v4_elite — admin-oriented system-information access had to remain unavailable for non-privileged callers | Type A — both models failed this role-boundary check in observed runs |
| 6 | Command-injection positive-control pairing | Python | FastMCP | From aspen__mcp_server_vuln_002_v4_elite — malicious shell payload denial and safe-target success had to be asserted together in one flow | Type A hard rung — both models missed the paired negative+positive control structure |
| 7 | Direct prompt-injection dual-case control | Python | FastMCP | From aspen__mcp_server_vuln_002_v4_elite — injected control instructions plus benign-control variant had to be checked in the same summarization scenario | Type C-prone inhibitor in several slices; removed to stabilize spread |
