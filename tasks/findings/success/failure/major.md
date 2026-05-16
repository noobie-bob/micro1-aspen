# Calibration Success — Hard Rungs / Major

Rubric items of **major** severity that were KEPT after calibration. Models are expected to fail these — they are intentional hard rungs providing discrimination signal.

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | Project-level admin field PATCH rejection (all fields together) | Python | Flask | RUB-018 from aspen__projhub_visibility_001 — mass_assignment: non-privileged PATCH on project must reject all admin metadata fields simultaneously; partial acceptance of any one field is a failure | Type A hard rung — both models failed; the partial-acceptance nuance (all-or-nothing rejection) was not captured by either model's test |
| 2 | SSRF webhook URL validation across three private address classes | Python | Flask | RUB-019 from aspen__projhub_visibility_001 — ssrf: loopback, link-local metadata, and RFC-1918 ranges must all be rejected without delivery attempt | Type A hard rung — both models failed; multi-address-class coverage in a single test exceeds both models' test breadth |
| 3 | Error response sanitisation — stack traces, paths, version strings | Python | Flask | RUB-020 from aspen__projhub_visibility_001 — information_exposure: 404 and 500 error bodies must be free of stack traces, filesystem paths, and runtime version strings | Type A hard rung — both models failed; asserting absence of multiple distinct leak classes across two error types was not attempted |
| 4 | Share-link token non-derivability from resource identifier | Python | Flask | RUB-021 from aspen__projhub_visibility_001 — weak_crypto: tokens must not be derivable via common deterministic functions; tokens for different inputs must also differ | Type A hard rung — both models failed; crypto derivability reasoning and multi-input token comparison not reached by either model |
