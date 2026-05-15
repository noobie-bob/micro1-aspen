# Realm Aspen: Reviews

## Peer QC

A peer reviewer will audit tasks before HDM/HDL sign-off to verify the following:

### Rubric & Prompt Integrity

- Rubric items are atomic and binary — each can be answered MET/UNMET on the agent's diff without multi-part interpretation.
- Both direct-coverage items and anti-overblock items are represented; anti-overblock is not collapsed into a single item.
- Concern categories are accurate; severity weights are calibrated.
- Prompt does not enumerate rubric items or list the structural axes the agent is expected to find.

### Technical Execution

- Dockerfile applies anti-cheating (single commit, no remote, fresh git init) with no pipeline-name leftovers.
- Smoke test correctly encodes the codebase's normal-operation surface (the public API in legitimate use), without prescribing the scenario-under-test.

### Calibration Distribution

- Data must show a spread of ~0.20, no saturation, top-of-frontier rung exists, distribution is well-behaved.
- Frontier model (opus 4.7) should achieve perfect score (1.0) on at least 1 run.
- Secondary model (Gemini 3.1 pro) should only achieve a passing score (1.0 or 100%) on at most 2/4 runs.

## Common Failure Modes

Tasks that come back from QC most often fail for one of these reasons:

- **Single-contract rubric:** All items are direct-coverage; no anti-overblock guards. Trivially satisfied by any test suite that over-asserts and would fail correct alternative implementations.
- **Saturated frontier:** opus-4.7 hits 1.00 at n=1. The rubric does not have enough headroom.
- **rubric_max_score arithmetic error:** The sum of severity weights doesn't match the field. Recompute on every rubric edit.
- **Pipeline-name leftover:** Strings like `shield.local` or `sequoia` in the Dockerfile, README, or commit message. Tells the reviewer the task was forked from a sibling pipeline without cleanup.
- **Smoke test missing or anemic:** Without a load-bearing smoke test, frontier models cannot induce the codebase's normal-operation surface, and reward floors.
- **Prompt leaks the rubric:** Enumerating the rubric items or structural axes in the prompt eliminates the scenario-induction signal — the agent doesn't have to think.

## HDM / HDL Sign-off

Final review by your Human Data Manager and Human Data Lead confirms ground-truth coverage and ship-readiness.

Sign-off is recorded in the Realm platform's QC review interface.

This check confirms the task is ready to be used in production training loops.
