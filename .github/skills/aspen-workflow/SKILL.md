---
name: aspen-workflow
description: "Aspen project directory layout, two-Dockerfile pattern (local vs production), chronological workflow phases (substrate, rubric, QC), what files ship to the agent vs stay local. Load when planning task structure, understanding which files go in which image, or reviewing the three workflow phases."
user-invocable: false
---

# Realm Aspen: Workflow

Tasks are built locally in an authoring folder and submitted as a bundled package. The folder must follow the naming convention: `aspen__{substrate}_{vulnerability_class}_{NNN}` (e.g., `aspen__taskhub_idor_001`).

## Project Directory Layout

Every task lives under `micro1-aspen/tasks/taskNN/` with **two Dockerfiles** serving different purposes:

```
micro1-aspen/tasks/taskNN/
├── .dockerignore                    # Exclude answer files from local Docker context
├── Dockerfile                       # LOCAL testing — copies substrate + ALL tests
├── requirements.txt                 # Pinned dependencies (language-dependent)
├── pytest.ini                       # Test runner config (language-dependent)
├── {substrate}/                     # The service source code (the "buggy" codebase)
│   ├── __init__.py
│   ├── app.py
│   ├── auth.py
│   ├── db.py
│   └── routes/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures — ships in BOTH images
│   ├── test_smoke.py                # Legitimate flow tests — LOCAL ONLY, NOT in production image
│   └── exfiltration/                # Gold-standard answer tests — LOCAL ONLY, never in any image
│       ├── __init__.py
│       ├── test_access_control.py
│       ├── test_injection.py
│       └── ...
└── aspen__{substrate}_{vuln}_{NNN}/ # Task config directory (submitted to platform)
    ├── prompt.txt                   # Agent-facing prompt
    ├── task_config.json             # Pipeline metadata + rubric
    ├── reasoning.txt                # Design rationale
    ├── README.md                    # Team-facing status + calibration data
    ├── DEEP_DIVE.md                 # Outsider on-ramp
    └── Dockerfile                   # PRODUCTION image — substrate + conftest ONLY
```

### Two Dockerfiles, Two Purposes

| File | What it copies | Purpose |
|------|---------------|---------|
| `taskNN/Dockerfile` | Substrate + ALL tests (smoke + exfiltration via `.dockerignore` exclusion) | Local testing and validation |
| `taskNN/aspen__*/Dockerfile` | Substrate + `conftest.py` ONLY | Production image pushed to Docker Hub — this is what the agent sees |

**Why separate?** The production image must contain NO pre-written tests. The agent writes ALL test files from scratch — including smoke tests and security tests. Only `conftest.py` ships because it provides shared fixtures (client, auth headers, data setup) that the agent's tests will import.

### What Each File Is For

| File | Shared with agent? | Purpose |
|------|-------------------|---------|
| `{substrate}/` | ✅ Yes (in image) | The buggy codebase the agent analyses |
| `tests/conftest.py` | ✅ Yes (in image) | Shared fixtures — client, auth headers, data setup topology |
| `tests/test_smoke.py` | ❌ No | Legitimate-flow tests for YOUR local validation only |
| `tests/exfiltration/` | ❌ No | Gold-standard answer tests for YOUR calibration only |
| `prompt.txt` | ✅ Yes (uploaded) | Agent reads this to understand the task |
| `task_config.json` | ✅ Yes (uploaded) | Agent sees the rubric descriptions (but NOT the test code) |
| `DEEP_DIVE.md` | ✅ Yes (uploaded) | Additional context for the agent |
| `reasoning.txt` | ❌ No | Internal design rationale |

## What You Submit

Upload the directory containing these six artifacts to the platform:

```
aspen__taskhub_idor_001/
├── prompt.txt
├── task_config.json
├── reasoning.txt
├── README.md
├── DEEP_DIVE.md
└── Dockerfile              # The PRODUCTION Dockerfile (no tests)
```

In addition, you must:

- **Push the Docker image:** Built from the PRODUCTION Dockerfile (`aspen__*/Dockerfile`), pushed to the private `micro1ai/` Docker Hub registry. Record the versioned tag and digest in `task_config.json` → `repo.image_name` and `repo.image_digest`. No `:latest` tags.
- **Run frontier triad calibration:** Capture per-model rewards, pass@k stats, and per-rubric catch rates in your `README.md` before submitting.

## Chronological Workflow Overview

### Phase 1: Substrate & Image Construction (~3–4 hrs)

1. **Substrate Construction:** Author or curate a small service (~300-1500 LOC) where the target test scenario is precisely scoped.
2. **Write conftest.py:** Create the shared fixtures (client, auth headers, data topology setup) that both your tests and the agent's tests will use.
3. **Write test_smoke.py (local only):** Encode the codebase's normal-operation surface. This stays local — the agent does NOT see it.
4. **De-annotate source code:** Remove all `# BUG:` comments, vulnerability labels, and revealing docstrings from the substrate.
5. **Build the Dockerfile(s):** Create both the local Dockerfile (with tests) and the production Dockerfile (substrate + conftest only).
6. **Validate locally:** Confirm conftest fixtures work, the scenario is observable, and there is no `.git` history beyond the single initial commit.

### Phase 2: Rubric Construction & Calibration (~3–4 hrs)

1. **Decompose the scenario:** Break the test scenario into atomic rubric items along structural axes (direct coverage and anti-overblock guards). 11-28 substantive items is a healthy range.
2. **Write the prompt:** Frame the task as a peer-to-peer bug report. Describe symptoms, not the inspection plan. Reference `conftest.py` for available fixtures — NOT `test_smoke.py`.
3. **Write behaviourally abstract rubric descriptions:** Describe observable behaviour, not specific field names, endpoint paths, or vulnerability mechanisms.
4. **Assign severities:** `critical=4, major=3, minor=2, nitpick=1`.
5. **Calibrate for separation:** Opus 4.7 ~75-85%, Qwen ~20-50%.

### Phase 3: Quality Control (~1–2 hrs)

1. **Peer review:** Verifies rubric atomicity, prompt integrity, conftest fixture surface, anti-cheating Dockerfile, and calibration data.
2. **HDM/HDL sign-off:** Final review for ground-truth coverage and ship-readiness.
