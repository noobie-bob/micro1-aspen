# Realm Aspen: Workflow

Tasks are built locally in an authoring folder and submitted as a bundled package. The folder must follow the naming convention: `aspen__{substrate}_{vulnerability_class}_{NNN}` (e.g., `aspen__taskhub_idor_001`).

## What you build locally (Authoring Folder)

```
aspen__taskhub_idor_001/
├── prompt.txt              Engineer-to-engineer prompt presented to the agent
├── task_config.json        Pipeline metadata, ground_truth_issues[], image ref
├── reasoning.txt           Task design rationale (threat model + rubric structure)
└── image_build/            Per-task Docker context (the agent's working env)
    ├── Dockerfile          Buggy starter image, anti-cheating measures applied
    ├── requirements.txt    Pinned dependencies - language dependent
    ├── pytest.ini          Test runner config - language dependent
    ├── {substrate}/        The service source (e.g., main/, app/, etc.) - language dependent
    └── tests/
        ├── conftest.py     Test fixtures (auth, client, etc.) - language dependent
        └── test_smoke.py   Legitimate participant + admin flows (load-bearing) - language dependent
```

`test_smoke.py` (or equivalent in other languages) is load-bearing. The smoke test file inside the image encodes the route-to-role mapping (which endpoints non-admin participants can call, which only admins can) naturalistically. Removing it floors model performance because the agent cannot induce the participant flow from the buggy router code alone. Every Aspen task ships one.

## What you submit

Upload the directory containing these six artifacts to our platform.

```
aspen__taskhub_idor_001/
├── prompt.txt
├── task_config.json
├── reasoning.txt
└── image_build/   	(the full Docker build context)
```

In addition, you must:

- **Push the Docker image:** Built from `image_build/Dockerfile`, pushed to the private `micro1ai/` Docker Hub registry. Record the versioned tag and digest in `task_config.json` → `repo.image_name` and `repo.image_digest`. No `:latest` tags.
- **Run frontier triad calibration:** Capture per-model rewards, pass@k stats, and per-rubric catch rates in your `README.md` before submitting.

## Chronological Workflow Overview

### Phase 1: Substrate & Image Construction (~3–4 hrs)

1. **Substrate Construction:** Author or curate a small service (~300-500 LOC) where the target test scenario is precisely scoped. This could be a feature to test, a known bug to regress, an edge case to exercise, etc.
   - Curated subsets of public repos are acceptable when the scenario is sharp and a public test suite for it isn't already searchable.
2. **Write the smoke test:** Encode the codebase's normal-operation surface in `tests/test_smoke.py`. This is a load-bearing file that teaches the agent how the public API behaves in legitimate use.
3. **Build the Dockerfile:** Apply anti-cheating measures with E2B convention: uid 1000 named user, `WORKDIR /repo`, fresh git init with a single commit, no remote (See Docker Setup section for the full template).
4. **Validate locally:** Confirm that: smoke tests pass, the scenario-under-test is observable from the agent's perspective, and there is no `.git` history beyond the single initial commit. Realm will also validate the successful image build.

### Phase 2: Rubric Construction & Calibration (~3–4 hrs)

1. **Decompose the scenario:** Break the test scenario into atomic rubric items along structural axes (direct coverage and anti-overblock guards).
   - The rubric includes both direct-coverage items and anti-overblock items (See the Rubric Taxonomy section).
2. **Write the prompt:** Frame the task as a peer-to-peer asking the agent to write a test suite. Explicitly forbid code modifications outside the test directory. This is important, as agents will sometimes write the implementation or fix instead.
3. **Assign severities:** Use the standard weights `critical=4, major=3, minor=2, nitpick=1`.

### Phase 3: Quality Control (~1–2 hrs)

1. **Peer review:** A second engineer verifies: rubric items are atomic and binary, prompt does not enumerate the rubric items, smoke test correctly encodes the legitimate flow surface, Dockerfile applies anti-cheating, and calibration data supports the DISCRIMINATIVE verdict.
2. **HDM/HDL sign-off:** Final review for ground-truth coverage and ship-readiness.
