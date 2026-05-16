# Trimmed Rubric Items — Pass / Major

Items removed during calibration where severity is **major** and both models passed (floor items with no discrimination value).

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | Cross-boundary resource fetch by opaque identifier | Python | Flask | access_control: direct-fetch by ID returns access-denied for cross-boundary resource | Type D floor — both models passed; no discrimination value |
| 2 | Cross-boundary child resource enumeration | Python | Flask | access_control: listing sub-resources of a cross-boundary parent is also denied — RUB-001 from aspen__projhub_visibility_001 | Type D floor — both models passed all runs; no discrimination value |
| 3 | Cross-boundary leaf resource direct read | Python | Flask | access_control: reading a leaf by direct ID returns 403 when parent belongs to another boundary — RUB-002 from aspen__projhub_visibility_001 | Type D floor — both models passed all runs |
| 4 | Cross-boundary write denial | Python | Flask | ownership: PATCH on another boundary's resource returns 403 — RUB-003 from aspen__projhub_visibility_001 | Type D floor — both models passed all runs |
