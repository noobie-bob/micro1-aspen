# task11 — Litestar Password-Recovery Lifecycle

Single-task Aspen pack for the Litestar password-recovery lifecycle scenario. The metadata folder still uses a legacy `authorisation-validation` slug, but the live prompt, rubric, and substrate all focus on reset-artifact supersession, replay resistance, and overlapping-client behavior.

Aspen is `rubric_only`: the model is graded on the test suite it authors against `ground_truth_issues[]`, not on an in-sandbox fix. The companion [DEEP_DIVE.md](DEEP_DIVE.md) is the outsider on-ramp; this README is the team-facing status report and calibration scratchpad.

## Tasks in this pack

| Task | Substrate | Rubric items | Status |
| --- | --- | --- | --- |
| `aspen__yamn_litestar_authorisation_validation_001` | Hand-authored Litestar in-memory auth service with stale reset-artifact lifecycle bug | 12 (9 critical + 3 major) | **DISCRIMINATIVE** — calibrated 2026-05-26 |

## Calibration results — `aspen__yamn_litestar_authorisation_validation_001`

Using the supplied calibration summary for 2026-05-26: `claude-opus-4-7` was evaluated once and `qwen` was evaluated over four runs. The reported miss sets are internally consistent with the weighted rubric: Opus catches 42/45 points (misses RUB-011) and Qwen averages 16/45 points (misses RUB-001, RUB-002, RUB-006, RUB-007, RUB-009, RUB-010, RUB-011, and RUB-012).

### Per-model summary

| Model | n | Mean | Saturate (=1.00) | Pass-rate (>=0.5) | Distribution |
| --- | :---: | :---: | :---: | :---: | --- |
| `claude-opus-4-7` | 1 | **0.933** | 0/1 | 1/1 | {0.933} |
| `qwen` | 4 | **0.356** | 0/4 | 0/4 | {0.356, 0.356, 0.356, 0.356} |

Frontier-mean spread = **0.578** (Opus 0.933 vs Qwen 0.356). No model saturates at 1.0, and the task cleanly separates frontier single-run coverage from mid-tier misses on cross-client and auth-matrix reasoning.

### qwen stability — N=4 pass@k

`pass@k = 1 - C(n - c, k) / C(n, k)`

The supplied calibration summary implies all four Qwen runs landed on the same 0.356 rung.

**Success threshold = reward >= 0.5** (`c = 0`):

| k | pass@k |
| :---: | :---: |
| 1 | **0.0000** |
| 2 | 0.0000 |
| 3 | 0.0000 |
| 4 | 0.0000 |

**Success threshold = reward = 1.0** (`c = 0`):

`c = 0` over N=4 -> **pass@k = 0 for all k in [1, 4]**. Qwen never reaches the task's midline, let alone full coverage, in the supplied run set.

### Per-rubric catch rates over N=5 (opus 1 + qwen 4)

| Rubric | Severity (weight) | Caught | Rate | Notes |
| --- | --- | :---: | :---: | --- |
| RUB-001 | critical (4) | 1/5 | **20%** | latest-only triple-request coverage is Opus-only |
| RUB-002 | critical (4) | 1/5 | **20%** | same shape as RUB-001 |
| RUB-003 | critical (4) | 5/5 | **100%** | fully saturated |
| RUB-004 | critical (4) | 5/5 | **100%** | replay-consumption check is saturated |
| RUB-005 | critical (4) | 5/5 | **100%** | older-token invalidation after success is saturated |
| RUB-006 | critical (4) | 1/5 | **20%** | cross-client supersession is Opus-only |
| RUB-007 | critical (4) | 1/5 | **20%** | final-password authority is Opus-only |
| RUB-008 | critical (4) | 5/5 | **100%** | concurrent single-winner coverage is saturated |
| RUB-009 | critical (4) | 1/5 | **20%** | loser-password auth denial is Opus-only |
| RUB-010 | major (3) | 1/5 | **20%** | stale-attempt side effects are Opus-only |
| RUB-011 | major (3) | 0/5 | **0%** | unreached auth-matrix top rung |
| RUB-012 | major (3) | 1/5 | **20%** | persistent-client modeling is Opus-only |

**Discrimination ladder rungs:**

- **Fully saturated (100%)**: RUB-003, RUB-004, RUB-005, RUB-008 — every supplied run catches the straightforward lifecycle integrity checks.
- **Frontier-only (20%)**: RUB-001, RUB-002, RUB-006, RUB-007, RUB-009, RUB-010, RUB-012 — Opus reaches these rungs and Qwen does not.
- **Unreached top rung (0%)**: RUB-011 — neither Opus nor Qwen authored the full post-recovery auth matrix assertion in the supplied sample.

### Discrimination interpretation

This calibration is strongly discriminative. Opus lands at **0.933** while Qwen averages **0.356**, a spread of **0.578** with no saturation. The middle of the rubric is stable, but the cross-client, loser-auth, and persistent-client behaviors split cleanly by model, while RUB-011 remains a true top rung that no supplied run reached.

Verdict: **DISCRIMINATIVE**

## Ground-truth rubric — `aspen__yamn_litestar_authorisation_validation_001`

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
| RUB-012 | major | persistent_client_model | Tests use independent persistent clients or cookie jars for multi-request and cross-client recovery behavior. |

## Per-task contents

```text
.
  README.md
  DEEP_DIVE.md
  reasoning.txt
  aspen-yamn-litestar-authorisation-validation/
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

`micro1ai/aspen-yamn-litestar:authorisation-validation-v1` (digest `sha256:b0b1b004e8fac5d087273c203aaebc90d77e092ab214bbfabe1297952126b1cc`).

Build metadata comes from `aspen-yamn-litestar-authorisation-validation/task_config.json`. `projhub/app.py` wires the typed Litestar handlers, seeds `alice@example.com` and `bob@example.com`, and exposes the outbox endpoint that tests use to capture issued artifacts through the real flow.

## Aspen pipeline gotchas

- Aspen is `rubric_only: true`, so there is no deterministic `FAIL_TO_PASS` verifier hiding behind these docs.
- The prompt must keep the agent in tests-only mode; otherwise strong models may try to “fix” `projhub/app.py` instead of codifying the lifecycle contract.
- `tests/test_smoke.py` and `/__test__/sent-reset-emails` are still load-bearing even though this variant does not give them their own rubric rows.
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
