# Trimmed Rubric Items — Failure / Major

Items removed during calibration where severity is **major** and both models failed (or Qwen outscored Opus — inverted signal).

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | Action-endpoint field-redaction bypass (clone/share/export) | Python | Flask | redaction: sentinel values must be absent from all three secondary data-access action endpoints | Type A — both models failed; too multi-step for current runs |
| 2 | Shell metacharacter injection in report generation | Python | Flask | command_injection: multiple metacharacter classes must each fail to produce shell execution evidence | Type A — both models failed; command injection too deep for calibration window |
| 3 | Deprecated route accessibility to unauthenticated and non-admin callers | Python | Flask | improper_assets: both legacy endpoints must return non-200 across all caller types | Type A — both models failed; legacy-asset coverage not reached |
| 4 | Mass-assignment multi-field PATCH rejection | Python | Flask | mass_assignment: non-privileged PATCH with multiple admin fields must be entirely rejected or ignored | Type A — both models failed; partial-acceptance nuance not tested |
| 5 | Deprecated MCP tool inaccessibility | Python | FastMCP | assets_management: legacy_dump tool must be removed or inaccessible; inverted signal (Qwen passed, Opus failed) | Type C (inverted) — Qwen outscored Opus; inhibitor removed |
| 6 | Admin tool access control — MCP server | Python | FastMCP | access_control: admin_sysinfo tool must require an admin token; inverted signal (Qwen passed, Opus failed) | Type C (inverted) — Qwen outscored Opus; inhibitor removed |
| 7 | Discussion thread filtering for non-privileged callers | Python | Flask | redaction: admin-audience comment entries must be absent both structurally and in raw body | Type A — both models failed consistently across all runs |
| 8 | Admin aggregate reporting endpoint access denial | Python | Flask | admin_endpoint: non-admin caller must receive access-denied from aggregate-report endpoint | Type C (inhibitor) — Opus failed in run 3 while Qwen passed 100%; flaky inhibitor removed |
| 9 | Mass-assignment admin-field PATCH rejection | Python | Flask | mass_assignment: admin metadata fields must be rejected on non-privileged PATCH | Type A — both models failed consistently across all runs |
| 10 | SSRF private-range URL validation | Python | Flask | ssrf: loopback, link-local, and RFC-1918 ranges must each be rejected | Type A — both models failed; multi-class SSRF too deep |
| 11 | Sanitised error responses (stack traces / paths / versions) | Python | Flask | information_exposure: stack traces and filesystem paths must be absent from 404 and 500 bodies | Type A — both models failed consistently |
| 12 | Non-derivable token generation | Python | Flask | weak_crypto: tokens must not be deterministically derivable from resource ID | Type A — both models failed; crypto reasoning too deep |
| 13 | Cross-boundary task-action endpoint access denial | Python | Flask | access_control: task assignment and status-transition must return 403 for cross-boundary caller | Type A — both models failed consistently |
