# Calibration Success — Validated / Critical

Rubric items of **critical** severity that were KEPT and validated during calibration. Opus passes, Qwen fails — these are the core discrimination signal items.

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | Search endpoint injection with data-extraction content check | Python | Flask | RUB-012 from aspen__projhub_visibility_001 — sql_injection: crafted payload must not cause privileged store data to appear in response body; assertion is content-level not status-code | Type B — Opus wrote injection payload + raw-body content check; Qwen did not reach content-level assertion |
| 2 | Credential-exposing diagnostic endpoint — multi-caller content check | Python | Flask | RUB-014 from aspen__projhub_visibility_001 — sensitive_data_exposure: diagnostic endpoint tested with both unauthenticated and non-admin callers; known credential values must be absent from response body | Type B — Opus covered both caller types and checked credential string absence; Qwen checked status code only or missed one caller type |
