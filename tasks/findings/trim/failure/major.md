# Trimmed Rubric Items — Failure / Major

Items removed during calibration where severity is **major** and both models failed (or Qwen outscored Opus — inverted signal).

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | Action-endpoint field-redaction bypass (clone/share/export) | Python | Flask | redaction: sentinel values must be absent from all three secondary data-access action endpoints | Type A — both models failed; too multi-step for current runs |
| 2 | Shell metacharacter injection in report generation | Python | Flask | command_injection: multiple metacharacter classes must each fail to produce shell execution evidence | Type A — both models failed; command injection too deep for calibration window |
| 3 | Deprecated route accessibility to unauthenticated and non-admin callers | Python | Flask | improper_assets: both legacy endpoints must return non-200 across all caller types | Type A — both models failed; legacy-asset coverage not reached |
| 4 | Mass-assignment multi-field PATCH rejection | Python | Flask | mass_assignment: non-privileged PATCH with multiple admin fields must be entirely rejected or ignored | Type A — both models failed; partial-acceptance nuance not tested |
