# Trimmed Rubric Items — Failure / Minor

Items removed during calibration where severity is **minor** and both models failed (or Qwen outscored Opus — inverted signal).

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | Path traversal via file download endpoint | Python | Flask | traversal: two traversal encoding methods plus cross-resource traversal must all be tested | Type A — both models failed; multi-encoding traversal coverage not reached |
