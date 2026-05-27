#!/usr/bin/env bash
# Oracle solution for Aspen: writes a placeholder unified-diff stub derived
# from the ground_truth_issues rubric. Used for sanity-checking the verifier
# pipeline; the judge inspects /repo/answer.diff as text and never applies it.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_oracle_rubric.py b/tests/exfiltration/test_oracle_rubric.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_oracle_rubric.py
@@ -0,0 +1,18 @@
+"""Oracle stub — one placeholder test per ground_truth_issues entry.
+
+These are not real tests; they exist only so the verifier pipeline can be
+exercised end-to-end. The judge will grade them as not-satisfying and emit
+reward=0.
+"""
+
+def test_oracle_stub_rub_001():
+    """MAJOR — RUB-001: A test asserts that a non-admin GET /tasks/{id} response does not contain the private sandbox_config fields (gold_patch_b64, task_config_b64,..."""
+    pass
+
+def test_oracle_stub_rub_002():
+    """MAJOR — RUB-002: A test asserts that a non-admin GET /coding-tasks (list endpoint) response redacts the private sandbox_config fields from every row."""
+    pass
+
+def test_oracle_stub_rub_003():
+    """MAJOR — RUB-003: A test asserts that a non-admin GET /tasks/{id}/files/{name} returns a 4xx for files that appear in sandbox_config.hidden_seed_files (per-task hidden-name..."""
+    pass
+
+def test_oracle_stub_rub_004():
+    """MAJOR — RUB-004: A test asserts that a non-admin GET /runs/{id}/artifacts (and /artifacts-zip) returns a 4xx when the run's model is a *_validation mode (e.g.,..."""
+    pass
+
+def test_oracle_stub_rub_005():
+    """MAJOR — RUB-005: A test asserts that a non-admin GET /runs/{id}/artifacts (and /artifacts-zip) returns a 4xx when the run's created_by does not match the calling..."""
+    pass
+
+def test_oracle_stub_rub_006():
+    """MAJOR — RUB-006: A test exercises the duplicate-then-PATCH laundering flow: a non-admin duplicates a task, then PATCHes the clone's name; the test asserts the PATCH response..."""
+    pass
+
+def test_oracle_stub_rub_007():
+    """MAJOR — RUB-007: A test exercises the duplicate-then-share laundering flow: a non-admin duplicates a task, then calls /tasks/{id}/share on the clone; the test asserts the..."""
+    pass
+
+def test_oracle_stub_rub_008():
+    """MAJOR — RUB-008: A test exercises the duplicate-then-export laundering flow: a non-admin duplicates a task, then calls GET /tasks/{id}/export on the clone; the test asserts..."""
+    pass
+
+def test_oracle_stub_rub_009():
+    """MAJOR — RUB-009: An anti-overblock test asserts that an admin GET /coding-tasks (list endpoint) STILL returns rows containing the private sandbox_config fields..."""
+    pass
+
+def test_oracle_stub_rub_010():
+    """MAJOR — RUB-010: Anti-overblock tests assert that a non-admin participant CAN still call /tasks/{id}/duplicate, /tasks/{id}/share, and /tasks/{id}/export on their own..."""
+    pass
+
+def test_oracle_stub_rub_011():
+    """MINOR — RUB-011: An anti-overblock test asserts that a non-admin GET /tasks/{id}/files/public_readme.md (or the equivalent public seed file) still returns 200 with the..."""
+    pass
+
+def test_oracle_stub_rub_012():
+    """MINOR — RUB-012: A test asserts that a non-admin cannot use path traversal (e.g., .. segments) in /tasks/{id}/files/{path} to reach .golden/ or other private subdirectories."""
+    pass
+
+def test_oracle_stub_rub_013():
+    """NITPICK — RUB-013: Tests seed sentinel marker bytes into private artifacts (gold patch, hidden seed files, validation run outputs) and assert those marker bytes do not appear..."""
+    pass
+

DIFF_EOF

echo "Wrote oracle answer.diff stub to /repo/answer.diff (13 placeholder tests)."
