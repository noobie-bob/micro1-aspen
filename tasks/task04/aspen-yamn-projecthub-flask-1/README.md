# aspen__projhub_flask_visibility

## Tasks in this pack

| Substrate | Stack | Rubric items | Max score | Status |
|-----------|-------|--------------:|----------:|--------|
| projecthub | Flask | 13 (4 critical, 7 major, 2 minor) | 41 | DRAFT |

## Substrate summary

ProjectHub is a role-based Flask benchmark service with teams, projects, tasks, comments, attachments, sharing, reporting, and operational tooling. The seeded scenario is a visibility/exposure problem that spans boundary checks, response shaping, delegated/share flows, debug/ops surfaces, and crafted-input search/formatter paths.

The service is compact (readable in one sitting) but intentionally broad across surfaces to force multi-actor, multi-surface test journeys. Legitimate product flows include same-team participant work, lead/admin flows, delegated sharing, duplicate/export, and reporting; the test suite must demonstrate leaks while preserving those positive flows.

**Vulnerability classes:** CWE-284, CWE-639, CWE-200, CWE-862, CWE-915, CWE-22, CWE-78, CWE-918, CWE-328, CWE-209

## Image

- **Tag:** micro1ai/aspen-yamn-projecthub-flask:security-v1
- **Digest:** sha256:b1f6f8bad85187b8a702da429f219a32cfc3de24f00b4fdac938b6ebb0755ba7
- **Base commit:** 54b6d7cab5a8c421d5ff7874a1d5f6d07d5c5668
- **Status:** draft — update before platform submission

## Calibration results

Calibration: pending. Use the per-rubric catch rates and discrimination ladder as the primary signals once model runs are available.

## Notes

- The agent sees `projhub/app.py`, `projhub/db.py`, and `tests/test_smoke.py` in the image.
- The prompt instructs: write tests only; do not modify any file under `projhub/`.
- Gold-standard answer tests must be placed under `tests/exfiltration/` and assert sentinel markers and anti-overblock flows.

## Per-task contents

- `README.md` — this file (team-facing status)
- `DEEP_DIVE.md` — outsider on-ramp: what is being graded and why it works
- `prompt.txt` — the 3-paragraph engineer-to-engineer ask
- `task_config.json` — ground_truth_issues[], image metadata, `rubric_only: true`
- `reasoning.txt` — task design rationale and severity arithmetic
- `image` build context — see top-level `Dockerfile` in the metadata folder

