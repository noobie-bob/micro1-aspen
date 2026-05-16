# Trimmed Rubric Items — Failure / Nitpick

Items removed during calibration where severity is **nitpick** and both models failed (or Qwen outscored Opus — inverted signal).

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | Sentinel marker assertion in non-privileged responses | Python | Flask | test_quality: verifying sentinel values absent from non-privileged bodies | Type C inhibitor — Opus failed, Qwen passed; inverted signal actively hurts spread |
