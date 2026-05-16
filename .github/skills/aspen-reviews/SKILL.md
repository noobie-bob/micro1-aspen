---
name: aspen-reviews
description: "Peer QC checklist, HDM/HDL sign-off criteria, common task failure modes (single-contract rubric, saturated frontier, prompt leakage, inflated rubric count, rubric_max_score arithmetic errors, pipeline-name leftovers). Load when reviewing a completed task, auditing rubric integrity, or diagnosing calibration failures."
user-invocable: false
---

# Realm Aspen: Reviews

## Peer QC

A peer reviewer audits tasks before HDM/HDL sign-off:

### Rubric & Prompt Integrity

- Rubric items are atomic and binary — each can be answered MET/UNMET without multi-part interpretation.
- Both direct-coverage items and anti-overblock items are represented; anti-overblock is NOT collapsed into a single item.
- Concern categories are accurate; severity weights are calibrated.
- Prompt does NOT enumerate rubric items or list the structural axes the agent is expected to find.
- Prompt does NOT name the exact route families, modules, or bug classes in a way that tells the agent where to look.
- Regression guards and hard items show test variety rather than repeating the same assertion pattern.
- Rubric size is justified by scenario variety (11-18 items normal; bigger suites must earn their size).

### Technical Execution

- Dockerfile applies anti-cheating (single commit, no remote, fresh git init) with no pipeline-name leftovers.

### Calibration Distribution

- Data must show a spread of ~0.20, no saturation, top-of-frontier rung exists.
- Opus 4.7 should average ~75-85%; occasional higher runs fine, but repeated 95-100% means the task is too easy.
- Qwen 3.5 should stay in the 20-50% range.

## Common Failure Modes

Tasks that come back from QC most often fail for one of these reasons:

- **Single-contract rubric:** All items are direct-coverage; no anti-overblock guards. Trivially satisfied by over-asserting test suites.
- **Saturated frontier:** Opus 4.7 hits 1.00 at n=1. The rubric lacks headroom.
- **Scenario too easy:** Qwen clears more than half the rubric because the task relies on one repeated assertion pattern or the prompt points directly at the answer.
- **Inflated rubric count:** Many items, but several are simple neighbors that don't add meaningful discrimination.
- **rubric_max_score arithmetic error:** Sum of severity weights doesn't match the field. Recompute on every rubric edit.
- **Pipeline-name leftover:** Strings like `shield.local` or `sequoia` in the Dockerfile, README, or commit message.
- **Prompt leaks the rubric:** Enumerating rubric items or structural axes eliminates the scenario-induction signal.
- **Prompt leaks the search space:** Telling the agent to inspect `debug`, `legacy`, `search`, `report`, etc. narrows the work too much.
- **Not enough test variety:** Suite is mostly one style of GET/assert-status checks, with little body inspection, mutation/read-back, secondary path coverage, or realistic regression guards.

## HDM / HDL Sign-off

Final review by Human Data Manager and Human Data Lead confirms ground-truth coverage and ship-readiness.

Sign-off is recorded in the Realm platform's QC review interface.
