# Deep Dive — task11 — Litestar Password-Recovery Lifecycle

> **Audience.** This file is the outsider on-ramp for someone who has not seen this task pack before. By the end, you should know what the model is graded on, what the seeded lifecycle bug looks like in code, and how to interpret the calibration sections once staging results are available.
>
> The companion `README.md` is the team-facing status report. Use that file for image metadata, rubric tables, and finalized calibration numbers.

## 1. Five-second summary

A model is asked to write hidden regression tests for a small Litestar auth service where password-reset artifacts are never properly superseded or consumed. The suite has to prove that only the newest artifact for `alice@example.com` should work, that stale or replayed artifacts fail, and that the real login flow still reflects the newest successful reset.

## 2. Why test-authoring is the right shape for this task

There is no single correct fix shape here. A developer could replace the list of artifacts with one current value, prune older entries on issuance, consume the winning artifact on success, or store versioned recovery state and reject anything stale. The important thing is the lifecycle contract: older artifacts cannot stay live next to newer ones, successful use must be one-time, and a correct fix must preserve the legitimate recovery and login path.

That makes test authoring the right evaluation target. A good suite captures the attack and the anti-overblock contract without locking the grader to any one implementation strategy.

## 3. The setup — what the agent sees

The agent opens a compact Litestar app in `projhub/app.py`. The same module seeds two in-memory users through `state.reset()`: `alice@example.com` with `old-password` and `bob@example.com` with `bob-password`. It also registers the typed public surface:

- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/password/forgot`
- `POST /auth/password/reset`
- `GET /__test__/sent-reset-emails`
- `POST /__test__/reset-state`

`tests/test_smoke.py` shows the baseline flow: Alice can log in with `old-password`, request a reset email, fetch the latest token from the outbox endpoint, and complete a reset successfully. The hidden suite must preserve that path while proving the lifecycle boundary around stale, superseded, replayed, and overlapping artifacts.

## 4. The rubric / scenario as code

The bug is concentrated in one short code path inside `projhub/app.py`:

```python
token = secrets.token_urlsafe(24)
user.reset_tokens.append(token)
state.sent_reset_emails.append({"email": user.email, "token": token})

if data.token in user.reset_tokens:
    user.password = data.new_password
    return {"ok": True}
```

`forgot_password()` issues a fresh artifact and appends it to `user.reset_tokens`, but it never invalidates earlier ones for the same account. `reset_password()` then loops over every user and accepts any token still present in the list. It updates the password and returns success without removing the winning token or clearing older siblings.

That creates the whole scenario:

- three sequential reset requests leave three live artifacts in memory
- a stale artifact can still change the password after a newer request exists
- a successful artifact can be replayed because it is never consumed
- overlapping or near-concurrent clients can race different artifacts against one account

The right hidden suite therefore has to drive the public routes, capture artifacts from `/__test__/sent-reset-emails`, submit stale and newest artifacts through `/auth/password/reset`, and confirm the final truth through `/auth/login`. This Litestar variant keeps the rubric compact by focusing directly on lifecycle-state reasoning plus the persistent-client guard.

## 5. Why this is realistic

Password-reset lifecycle bugs are common because the happy path is easy to implement and the edge cases are not. Teams add “forgot password” support, confirm that one token works once in local testing, and stop there. Problems surface later when users request multiple reset emails, switch devices mid-flow, or click an older email after a newer one was issued.

The implementation shape here is realistic too: typed request models, straightforward route handlers, an outbox-like test seam, and no explicit token state machine. Those shortcuts are exactly how supersession and one-time-use guarantees get dropped in real services.

## 6. How calibration runs work

Aspen scores this as a rubric-only task. The platform turns each `ground_truth_issues[]` entry into a weighted criterion, then judges whether the authored tests cover that behavior.

The score formula is:

```text
reward = sum(score_i * weight_i) / rubric_max_score
```

For this Litestar variant, `rubric_max_score` is 45 because the rubric has 9 critical items and 3 major items:

```text
9 * 4 + 3 * 3 = 45
```

No verified staging results are stored in this folder yet, so this section explains the mechanics rather than a finalized model spread.

## 7. What the calibration revealed

The supplied 2026-05-26 calibration summary shows a strong split on the Litestar variant. `claude-opus-4-7` scores **0.933** on its single run, missing only RUB-011. Qwen averages **0.356** across four runs and repeatedly misses RUB-001, RUB-002, RUB-006, RUB-007, RUB-009, RUB-010, RUB-011, and RUB-012. That is not noise: it is a stable pattern where Qwen clears the direct lifecycle checks but drops the stricter latest-only, overlapping-client, loser-auth, and persistent-client assertions.

The catch-rate table has three distinct bands. RUB-003, RUB-004, RUB-005, and RUB-008 are fully saturated. RUB-001, RUB-002, RUB-006, RUB-007, RUB-009, RUB-010, and RUB-012 are frontier-only rungs, reached by Opus and missed by Qwen across the supplied sample. RUB-011 is the true top rung at **0/5**: nobody wrote the complete post-recovery auth matrix assertion. That gives this task a wide spread while still leaving one deliberately hard edge above the frontier run.

## 8. How to read the calibration numbers

Once the README has real numbers, read them in this order:

- Per-model mean: how much of the weighted lifecycle contract a model captures on average
- Saturation count: whether a model is reaching perfect coverage or still missing important edges
- Pass@k: how often repeated attempts reach a threshold such as `>= 0.5` or `= 1.0`
- Per-rubric catch rates: which exact lifecycle behaviors are consistently covered or consistently missed
- Discrimination ladder: whether the task has easy, medium, and hard rungs instead of collapsing to all-or-nothing

If a model catches only the easy stale-token checks but misses cross-client and concurrent single-winner behavior, the task is still doing useful discrimination. If every model saturates, the task is under-calibrated. If scores bounce randomly without a stable catch-rate pattern, the task is flaky.

## 9. What this rubric does not measure

This task does not try to grade every possible account-recovery concern. It does not measure rate limiting, token entropy, email-delivery infrastructure, long-term persistence, or database cleanup. It also does not require a particular storage design. The rubric is intentionally scoped to lifecycle correctness for issued artifacts and the legitimacy of the supported recovery path.

## 10. Glossary

- **Artifact**: the reset token issued by `POST /auth/password/forgot`
- **Newest artifact**: the last token currently visible in `/__test__/sent-reset-emails` for the account
- **Stale artifact**: any older token that should have been superseded by a newer request
- **Replay**: reusing a token after it has already completed a successful reset
- **Persistent client**: a separate client or cookie jar that carries its own request history through a multi-step flow
