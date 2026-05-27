# Aspen test-authoring task

A participant on our eval platform pinged me — they think they can read back files from tasks they didn't create. Said they were "poking around the API" with their normal participant key and stumbled into something that looked like another author's gold patch. They've been trying different things and keep finding stuff they shouldn't.

We don't have any tests covering this. Your job is to write the test suite that catches it.

**Write tests only. Do not modify any file under `taskhub/`.** A separate engineer will use your tests to validate their fix; for them to trust your tests, the suite must (1) catch the leak the participant is exploiting and (2) catch a fix that over-blocks legitimate participant or admin flows.

Put your tests under `tests/exfiltration/`. `tests/test_smoke.py` shows the legitimate participant + admin flows already in use — your suite should pin those down with anti-overblock assertions so they cannot regress.

Submit only your test files as a unified diff via `submit_answer` (applies clean from `/repo`).


## Working environment

- The repository is checked out at `/repo` at the task's `base_commit`.
- This is a **test-authoring** task. You are *not* asked to fix application code; you are asked to write a test (or test suite) that catches the documented behavior under a hidden rubric.

- Your tests are expected to land under: `tests/exfiltration/`.


## What to submit

Write a unified diff of the test file(s) you would add to the repo, and save that diff (as text) to `/repo/answer.diff`. The verifier reads only `/repo/answer.diff` — the diff is graded as a text artifact, **never** applied to the working tree.

The diff should follow standard `diff --git` format, e.g.:

```
diff --git a/path/to/new_test.py b/path/to/new_test.py
new file mode 100644
--- /dev/null
+++ b/path/to/new_test.py
@@ -0,0 +1,N @@
+# test body...
```

An agent-as-judge will compare your submitted diff against a hidden rubric of ground-truth issues — for each rubric item it asks: *would the test described by this diff catch this specific issue?*
