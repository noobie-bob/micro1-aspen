# Calibration Success — Hard Rungs / Critical

Rubric items of **critical** severity that were KEPT after calibration. Models are expected to fail these — they are intentional hard rungs providing top-of-frontier discrimination signal.

| Sl.No | Task Title | Language | Framework | Task Details | Reason |
|---|---|---|---|---|---|
| 1 | Delegated access expiry and invalid-state confinement | Go | net/http | RUB-003 from aspen__projecthub_visibility_003 — delegated_scope: shared access must stay confined to the granted workspace, fail on neighbouring resources, and stop working once the delegated state is expired, invalid, or incomplete | Type A hard rung — both models missed the invalid/expired delegated-state failure semantics and replay-confinement chain |
