# task08 — Flask Password-Recovery Lifecycle

Single-task Aspen pack for the Flask password-recovery lifecycle scenario. The metadata folder still carries a legacy `authorisation-validation` slug, but the live prompt, rubric, and substrate all evaluate reset-artifact supersession, replay resistance, and overlapping-client behavior.

Aspen is `rubric_only`: the model is graded on the test suite it authors against `ground_truth_issues[]`, not on an in-sandbox fix. The companion [DEEP_DIVE.md](DEEP_DIVE.md) is the outsider on-ramp; this README is the team-facing status report and calibration scratchpad.

## Tasks in this pack

| Task | Substrate | Rubric items | Status |
| --- | --- | --- | --- |
| `aspen__yamn_flask_authorisation_validation_001` | Hand-authored Flask in-memory auth service with stale reset-artifact lifecycle bug | 14 (9 critical + 5 major) | **DISCRIMINATIVE** — calibrated 2026-05-26 |

## Calibration results — `aspen__yamn_flask_authorisation_validation_001`

Using the supplied calibration summary for 2026-05-26: `claude-opus-4-7` was evaluated once and `qwen` was evaluated over four runs. The reported miss sets are internally consistent with the weighted rubric: Opus catches 43/51 points (misses RUB-001 and RUB-002) and Qwen averages 26/51 points (misses RUB-004, RUB-006, RUB-007, RUB-009, RUB-010, RUB-011, and RUB-014).

### Per-model summary

| Model | n | Mean | Saturate (=1.00) | Pass-rate (>=0.5) | Distribution |
| --- | :---: | :---: | :---: | :---: | --- |
| `claude-opus-4-7` | 1 | **0.843** | 0/1 | 1/1 | {0.843} |
| `qwen` | 4 | **0.510** | 0/4 | 4/4 | {0.510, 0.510, 0.510, 0.510} |

Frontier-mean spread = **0.333** (Opus 0.843 vs Qwen 0.510). No model saturates at 1.0, but Opus clears the frontier bar while Qwen stalls on the replay and overlapping-client rungs.

### qwen stability — N=4 pass@k

`pass@k = 1 - C(n - c, k) / C(n, k)`

The supplied calibration summary implies all four Qwen runs landed on the same 0.510 rung.

**Success threshold = reward >= 0.5** (`c = 4`):

| k | pass@k |
| :---: | :---: |
| 1 | **1.0000** |
| 2 | 1.0000 |
| 3 | 1.0000 |
| 4 | 1.0000 |

**Success threshold = reward = 1.0** (`c = 0`):

`c = 0` over N=4 -> **pass@k = 0 for all k in [1, 4]**. Qwen consistently reaches the middle rung of the rubric, but never approaches perfect coverage on this task.

### Per-rubric catch rates over N=5 (opus 1 + qwen 4)

| Rubric | Severity (weight) | Caught | Rate | Notes |
| --- | --- | :---: | :---: | --- |
| RUB-001 | critical (4) | 4/5 | **80%** | Opus misses the latest-only triple-request assertion; Qwen catches it |
| RUB-002 | critical (4) | 4/5 | **80%** | same shape as RUB-001 |
| RUB-003 | critical (4) | 5/5 | **100%** | fully saturated |
| RUB-004 | critical (4) | 1/5 | **20%** | Qwen blind spot on replay-consumption checks |
| RUB-005 | critical (4) | 5/5 | **100%** | fully saturated |
| RUB-006 | critical (4) | 1/5 | **20%** | overlapping-client supersession is Opus-only |
| RUB-007 | critical (4) | 1/5 | **20%** | final-password authority is Opus-only |
| RUB-008 | critical (4) | 5/5 | **100%** | concurrent single-winner check is saturated |
| RUB-009 | critical (4) | 1/5 | **20%** | losing-artifact auth denial is Opus-only |
| RUB-010 | major (3) | 1/5 | **20%** | stale-attempt side effects are a Qwen blind spot |
| RUB-011 | major (3) | 1/5 | **20%** | post-recovery auth matrix is a Qwen blind spot |
| RUB-012 | major (3) | 5/5 | **100%** | latest-artifact happy path stays visible |
| RUB-013 | major (3) | 5/5 | **100%** | real outbox capture path is saturated |
| RUB-014 | major (3) | 1/5 | **20%** | persistent-client modeling is Opus-only |

**Discrimination ladder rungs:**

- **Fully saturated (100%)**: RUB-003, RUB-005, RUB-008, RUB-012, RUB-013 — every supplied run catches the straightforward stale/newest and supported-flow checks.
- **Frontier-leaning (80%)**: RUB-001, RUB-002 — Qwen gets the latest-only sequence, but Opus misses the strict triple-request coverage once.
- **Hard rungs (20%)**: RUB-004, RUB-006, RUB-007, RUB-009, RUB-010, RUB-011, RUB-014 — replay, cross-client authority, auth-matrix, and persistent-client reasoning are effectively Opus-only.

### Discrimination interpretation

This calibration produces a clear two-tier split. Opus clears the task at **0.843** while Qwen averages **0.510**, a spread of **0.333** with no saturation on either side. Qwen is slightly above the ideal mid-tier ceiling, but its misses are concentrated in the right places: replay invalidation, overlapping-client supersession, final-password authority, and persistent-client modeling.

Verdict: **DISCRIMINATIVE**

## Ground-truth rubric — `aspen__yamn_flask_authorisation_validation_001`

| ID | Severity | Category | Criterion |
| --- | --- | --- | --- |
| RUB-001 | critical | three_artifact_latest_only | A test creates three distinct recovery artifacts for the same account through the real recovery flow and proves only the third/newest artifact can complete recovery. |
| RUB-002 | critical | all_prior_artifacts_rejected | A test proves both earlier artifacts from a three-artifact sequence are rejected and cannot change the password. |
| RUB-003 | critical | stale_attempt_preserves_latest | A test attempts recovery with a stale artifact, then proves the current newest artifact is still usable afterward. |
| RUB-004 | critical | used_latest_consumes_itself | A test completes recovery with the newest artifact, then proves that exact newest artifact cannot be reused. |
| RUB-005 | critical | used_latest_keeps_older_invalid | A test completes recovery with the newest artifact, then proves all older superseded artifacts remain unusable afterward. |
| RUB-006 | critical | cross_client_supersession | A test uses two independent clients where client A obtains an artifact, client B obtains a newer artifact for the same account, and client A's older artifact is rejected. |
| RUB-007 | critical | cross_client_final_password_authority | A test uses independent clients in overlapping recovery flows and proves the final account password can only be set by the newest valid artifact. |
| RUB-008 | critical | concurrent_single_winner | A test issues concurrent or near-concurrent recovery requests and proves exactly one resulting artifact can complete recovery. |
| RUB-009 | critical | concurrent_losers_cannot_authenticate | A test proves passwords attempted through losing or stale concurrent artifacts cannot be used to authenticate. |
| RUB-010 | major | stale_artifact_no_side_effects | A test proves a failed stale-artifact recovery attempt does not change password state, invalidate the newest artifact, or corrupt later login behavior. |
| RUB-011 | major | post_recovery_auth_matrix | A test verifies the authentication matrix after recovery: old password fails, stale-artifact password fails, and newest-artifact password succeeds. |
| RUB-012 | major | latest_artifact_success_regression | A test verifies the newest valid recovery artifact still completes the legitimate recovery flow successfully. |
| RUB-013 | major | real_mail_or_route_artifact_capture | Tests obtain recovery artifacts through the application's public recovery route, mail outbox, or documented smoke-test capture path rather than inserting valid tokens directly into storage. |
| RUB-014 | major | persistent_client_model | Tests use independent persistent clients or cookie jars for multi-request and cross-client recovery behavior. |

## Per-task contents

```text
.
  README.md
  DEEP_DIVE.md
  reasoning.txt
  aspen-yamn-flask-authorisation-validation/
    prompt.txt
    task_config.json
    Dockerfile
  projhub/
    app.py
  tests/
    conftest.py
    test_smoke.py
```

## Image

`micro1ai/aspen-yamn-flask:authorisation-validation-v1` (digest `sha256:7cc078f2ea2a15beaffb9774e27da44bb73833e98ff14e2250b53a6b07d5541d`).

Build metadata comes from `aspen-yamn-flask-authorisation-validation/task_config.json`. `projhub/app.py` seeds `alice@example.com` and `bob@example.com`, exposes the login and password-recovery routes, and keeps the outbox endpoint that tests use to capture issued artifacts without mutating storage directly.

## Aspen pipeline gotchas

- Aspen is `rubric_only: true`, so there is no deterministic `FAIL_TO_PASS` verifier hiding behind these docs.
- The prompt must keep the agent in tests-only mode; otherwise strong models may try to “fix” `projhub/app.py` instead of codifying the lifecycle contract.
- `tests/test_smoke.py` and `/__test__/sent-reset-emails` are load-bearing because they show the supported reset flow and the intended artifact-capture path.
- Cross-client rubric items are only meaningful if the authored suite uses separate persistent clients rather than one stateless helper.

## Verifying on staging

```bash
STAGING_KEY=...
STAGING=https://micro-openenvs-api-staging-502417714596.us-central1.run.app
TASK=<staging-task-id>

curl -X POST -H "Authorization: Bearer $STAGING_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"claude-opus-4-7"}' \
     "$STAGING/tasks/$TASK/eval"
```

Replace `TASK` with the staged Aspen task id for this folder, then backfill the calibration tables above from the recorded run set.

## Related repos

- [../gold-sample-aspen-main/README.md](../gold-sample-aspen-main/README.md) — gold-sample README shape and calibration table layout
- [../gold-sample-aspen-main/DEEP_DIVE.md](../gold-sample-aspen-main/DEEP_DIVE.md) — outsider on-ramp reference for deep-dive structure
