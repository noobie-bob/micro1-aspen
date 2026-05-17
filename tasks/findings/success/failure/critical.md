# Calibration Success — Hard Rungs / Critical

Rubric items of **critical** severity that were KEPT after calibration. Models are expected to fail these — they are intentional hard rungs providing top-of-frontier discrimination signal.

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | Delegated access expiry and invalid-state confinement | Go | net/http | RUB-003 from aspen__projecthub_visibility_003 — delegated_scope: shared access must stay confined to the granted workspace, fail on neighbouring resources, and stop working once the delegated state is expired, invalid, or incomplete | Type A hard rung — both models missed the invalid/expired delegated-state failure semantics and replay-confinement chain |
| 2 | Internal URL egress isolation in asset retrieval | Python | FastMCP | RUB-003 from aspen__mcp_server_vuln_002_v4_elite — fetch_project_asset must reject internal URL targets and avoid performing outbound access on blocked targets | Type A hard rung — both models failed this chained network-safety condition |
| 3 | Privileged surface enforcement across caller classes | Python | FastMCP | RUB-010 from aspen__mcp_server_vuln_002_v4_elite — privileged tools must be denied for both unauthenticated and non-admin callers with response-content checks, not exception-only checks | Type A hard rung — both models failed the coupled multi-caller assertions |
| 4 | Cross-tool SSRF chaining prevention | Python | FastMCP | RUB-015 from aspen__mcp_server_vuln_002_v4_elite — outputs from one tool must not be reusable to trigger SSRF via another tool in a multi-step attack chain | Type A hard rung — both models failed the chained exploit path verification |
