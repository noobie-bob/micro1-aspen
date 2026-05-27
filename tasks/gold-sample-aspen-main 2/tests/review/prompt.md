You are an experienced staff engineer evaluating whether a unified-diff submission contains tests that would catch a known set of ground-truth issues.

## Task background

This is an Aspen **test-authoring** task. The agent was *not* asked to fix application code; it was asked to write tests that would catch a hidden rubric of issues. The base repo is checked out at `/repo` at the task's `base_commit`.

## Behavioral prompt the agent received

```
A participant on our eval platform pinged me — they think they can read back files from tasks they didn't create. Said they were "poking around the API" with their normal participant key and stumbled into something that looked like another author's gold patch. They've been trying different things and keep finding stuff they shouldn't.

We don't have any tests covering this. Your job is to write the test suite that catches it.

**Write tests only. Do not modify any file under `taskhub/`.** A separate engineer will use your tests to validate their fix; for them to trust your tests, the suite must (1) catch the leak the participant is exploiting and (2) catch a fix that over-blocks legitimate participant or admin flows.

Put your tests under `tests/exfiltration/`. `tests/test_smoke.py` shows the legitimate participant + admin flows already in use — your suite should pin those down with anti-overblock assertions so they cannot regress.

Submit only your test files as a unified diff via `submit_answer` (applies clean from `/repo`).

```

## Where the agent's submission lives

The agent's submission is a unified-diff **text artifact** at `/repo/answer.diff` (relative to `/repo`: `answer.diff`).

You may read that file (and any sibling notes such as `notes.md`) and run read-only commands inside `/repo`. **Do not apply the diff and do not modify the workspace.** The diff is graded as text — what matters is whether the test code described in the diff *would* catch each rubric item if it were applied.


The submission is expected to touch the following path prefixes (a hint, not a hard requirement): `tests/exfiltration/`.


## Ground-truth rubric (hidden from the agent)

The criteria are listed below. For each one, decide **binary**: does the diff include a test (or assertion within a test) that would specifically catch this issue, with enough precision (right endpoint / right invariant / right boundary condition) that a real regression of this issue would fail the test? Generic smoke tests, vacuously-passing assertions, or tests that only exercise the legitimate flow without anti-overblock checks do **not** count.

If the diff contains test code that would break legitimate flows (over-blocks), that test still does **not** earn a point for any rubric item — and any explicit anti-overblock rubric items must fail.

{criteria}
