# Trimmed Rubric Items — Failure / Critical

Items removed during calibration where severity is **critical** and both models failed (or Qwen outscored Opus — inverted signal).

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | SQL injection via keyword search endpoint | Python | Flask | sql_injection: crafted payload must not cause privileged data to appear in response | Type A — both models failed; second-order injection reasoning too deep |
