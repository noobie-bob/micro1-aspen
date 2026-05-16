# Realm Aspen: Reviews

## Peer QC

A peer reviewer will audit tasks before HDM/HDL sign-off to verify the following:

### Rubric & Prompt Integrity

- Rubric items are atomic and binary — each can be answered MET/UNMET on the agent's diff without multi-part interpretation.
- Both direct-coverage items and anti-overblock items are represented; anti-overblock is not collapsed into a single item.
- Concern categories are accurate; severity weights are calibrated.
- Prompt does not enumerate rubric items or list the structural axes the agent is expected to find.
- Prompt does not name the exact route families, modules, or bug classes in a way that tells the agent where to look.
- Regression guards and hard items show test variety rather than repeating the same assertion pattern across adjacent endpoints.
- Rubric size is justified by scenario variety. Around 11-18 items is normal; bigger suites must earn their size with meaningfully different checks.

### Technical Execution

- Dockerfile applies anti-cheating (single commit, no remote, fresh git init) with no pipeline-name leftovers.

### Calibration Distribution

- Data must show a spread of ~0.20, no saturation, top-of-frontier rung exists, distribution is well-behaved.
- Frontier model (opus 4.7) should usually average around 75-85%; occasional higher runs are fine, but repeated 95-100% runs suggest the task is too easy.
- Secondary model (Qwen 3.5 or Gemini 3.1 Pro) should usually stay in the 20-50% range.

## Common Failure Modes

Tasks that come back from QC most often fail for one of these reasons:

- **Single-contract rubric:** All items are direct-coverage; no anti-overblock guards. Trivially satisfied by any test suite that over-asserts and would fail correct alternative implementations.
- **Saturated frontier:** opus-4.7 hits 1.00 at n=1. The rubric does not have enough headroom.
- **Scenario too easy:** Qwen or another mid-tier model clears more than half the rubric because the task relies on one repeated assertion pattern or the prompt points directly at the answer.
- **Inflated rubric count:** The task has many items, but several are simple neighbors of each other and do not add meaningful discrimination.
- **rubric_max_score arithmetic error:** The sum of severity weights doesn't match the field. Recompute on every rubric edit.
- **Pipeline-name leftover:** Strings like `shield.local` or `sequoia` in the Dockerfile, README, or commit message. Tells the reviewer the task was forked from a sibling pipeline without cleanup.
- **Prompt leaks the rubric:** Enumerating the rubric items or structural axes in the prompt eliminates the scenario-induction signal — the agent doesn't have to think.
- **Prompt leaks the search space:** Telling the agent to inspect `debug`, `legacy`, `search`, `report`, etc. in the prompt narrows the work too much and collapses the calibration gap.
- **Not enough test variety:** The suite is mostly one style of GET/assert-status check, with little body inspection, mutation/read-back, secondary path coverage, or realistic regression guards.

## HDM / HDL Sign-off

Final review by your Human Data Manager and Human Data Lead confirms ground-truth coverage and ship-readiness.

Sign-off is recorded in the Realm platform's QC review interface.

This check confirms the task is ready to be used in production training loops.
