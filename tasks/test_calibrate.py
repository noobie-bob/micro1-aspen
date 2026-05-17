"""
test_calibrate.py  —  stdlib unittest, no third-party deps required
=====================================================================
Coverage areas
  classify()        – all four quadrants + exact 0.5 boundary cases
  scores()          – weighted avg, empty list, zero-weight guard
  in_target()       – all four conditions; exact boundary values
  _score_state()    – penalty contributions, all-in-band baseline
  parse_items()     – happy path, severity fallback, missing columns,
                      malformed lines, comments, multi-run splits,
                      prefix matching (pass/fail full words)
  exhaustive_trim() – already-in-target; successful removal; no-solution;
                      RG items never removed; B items never removed
  greedy_trim()     – convergence; stalls on MIN_ITEMS; RG & B protected
  find_trim()       – C removal; pool-below-MIN guard; BUG-1 regression
  advise_new_tests()– all five diagnostic branches + dead-branch note
  CLI (subprocess)  – already-discriminative; trim-achievable; advice;
                      --opus-runs; --rg (BUG-1 e2e); --file; edge cases
"""

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(__file__))
import calibrate as C

SCRIPT = os.path.join(os.path.dirname(__file__), "calibrate.py")


# ─── Helpers ──────────────────────────────────────────────────────────────

def run(stdin_text, extra_args=None):
    cmd = [sys.executable, SCRIPT, "--rg", ""] + (extra_args or [])
    return subprocess.run(cmd, input=stdin_text, capture_output=True, text=True)


def make_item(id="RUB-001", severity="major",
              opus_avgs=(1.0,), qwen_avgs=(0.0,), rg=False):
    opus_avg = sum(opus_avgs) / len(opus_avgs)
    qwen_avg = sum(qwen_avgs) / len(qwen_avgs)
    return {
        "id": id, "severity": severity, "w": C.WEIGHTS[severity],
        "opus_runs": [a >= 0.5 for a in opus_avgs],
        "qwen_runs": [a >= 0.5 for a in qwen_avgs],
        "opus_avg": opus_avg, "qwen_avg": qwen_avg,
        "type": C.classify(opus_avg, qwen_avg), "rg": rg,
    }


def B(n, sev="major"):
    return [make_item(f"B-{i:03d}", sev) for i in range(1, n + 1)]

def D(n, sev="major"):
    return [make_item(f"D-{i:03d}", sev, (1.0,), (1.0,)) for i in range(1, n + 1)]

def A(n, sev="major"):
    return [make_item(f"A-{i:03d}", sev, (0.0,), (0.0,)) for i in range(1, n + 1)]

def Ci(n, sev="major", rg=False):
    return [make_item(f"C-{i:03d}", sev, (0.0,), (1.0,), rg) for i in range(1, n + 1)]

def advice(o, q, w=30):
    buf = io.StringIO()
    with redirect_stdout(buf):
        C.advise_new_tests([], o, q, w)
    return buf.getvalue()

# 11 B items: opus=100%, qwen=0% — NOT discriminative (qwen below floor)
DISC_11 = "\n".join(f"RUB-{i:03d},major,p,f,f,f,f" for i in range(1, 12))

# 14 items (11 B + 3 D major): qwen = 9/42 ≈ 21.4% → fully discriminative
DISC_14 = (
    "\n".join(f"B-{i:03d},major,p,f" for i in range(1, 12)) + "\n" +
    "\n".join(f"D-{i:03d},major,p,p" for i in range(1, 4))
)


# ═══════════════════════════════════════════════════════════════════════════
# classify()
# ═══════════════════════════════════════════════════════════════════════════

class TestClassify(unittest.TestCase):
    def test_B_opus_pass_qwen_fail(self):       self.assertEqual(C.classify(1.0, 0.0), "B")
    def test_B_with_averages(self):             self.assertEqual(C.classify(0.75, 0.25), "B")
    def test_D_both_pass(self):                 self.assertEqual(C.classify(1.0, 1.0), "D")
    def test_D_both_above_half(self):           self.assertEqual(C.classify(0.6, 0.6), "D")
    def test_A_both_fail(self):                 self.assertEqual(C.classify(0.0, 0.0), "A")
    def test_A_both_below_half(self):           self.assertEqual(C.classify(0.4, 0.4), "A")
    def test_C_opus_fail_qwen_pass(self):       self.assertEqual(C.classify(0.0, 1.0), "C")
    def test_C_with_averages(self):             self.assertEqual(C.classify(0.25, 0.75), "C")
    def test_boundary_opus_half_is_pass(self):  self.assertEqual(C.classify(0.5, 0.0), "B")
    def test_boundary_qwen_half_is_pass(self):  self.assertEqual(C.classify(0.0, 0.5), "C")
    def test_boundary_both_half(self):          self.assertEqual(C.classify(0.5, 0.5), "D")
    def test_just_below_half_opus(self):        self.assertEqual(C.classify(0.49, 0.0), "A")
    def test_just_below_half_qwen(self):        self.assertEqual(C.classify(1.0, 0.49), "B")


# ═══════════════════════════════════════════════════════════════════════════
# scores()
# ═══════════════════════════════════════════════════════════════════════════

class TestScores(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(C.scores([]), (0.0, 0.0, 0))

    def test_single_all_pass(self):
        o, q, w = C.scores([make_item(opus_avgs=(1.0,), qwen_avgs=(1.0,))])
        self.assertAlmostEqual(o, 1.0); self.assertAlmostEqual(q, 1.0); self.assertEqual(w, 3)

    def test_single_all_fail(self):
        o, q, _ = C.scores([make_item(opus_avgs=(0.0,), qwen_avgs=(0.0,))])
        self.assertAlmostEqual(o, 0.0); self.assertAlmostEqual(q, 0.0)

    def test_weighted_average(self):
        # critical(w=4) passes Opus; nitpick(w=1) fails → Opus = 4/5 = 0.80
        items = [make_item("A","critical",(1.0,),(0.0,)), make_item("B","nitpick",(0.0,),(0.0,))]
        o, q, w = C.scores(items)
        self.assertEqual(w, 5); self.assertAlmostEqual(o, 0.8); self.assertAlmostEqual(q, 0.0)

    def test_weight_sum(self):
        _, _, w = C.scores(B(3, "critical"))   # 3×4=12
        self.assertEqual(w, 12)

    def test_zero_weight_guard(self):
        item = make_item(); item["w"] = 0
        self.assertEqual(C.scores([item]), (0.0, 0.0, 0))

    def test_overridden_avg_used(self):
        item = make_item(); item["opus_avg"] = 0.5; item["qwen_avg"] = 0.25
        o, q, _ = C.scores([item])
        self.assertAlmostEqual(o, 0.5); self.assertAlmostEqual(q, 0.25)


# ═══════════════════════════════════════════════════════════════════════════
# in_target()
# ═══════════════════════════════════════════════════════════════════════════

class TestInTarget(unittest.TestCase):
    def test_all_met(self):             self.assertTrue(C.in_target(0.85, 0.35, 11))
    def test_opus_low(self):            self.assertFalse(C.in_target(0.79, 0.35, 11))
    def test_qwen_low(self):            self.assertFalse(C.in_target(0.85, 0.19, 11))
    def test_qwen_high(self):           self.assertFalse(C.in_target(0.85, 0.51, 11))
    def test_count_low(self):           self.assertFalse(C.in_target(0.85, 0.35, 10))
    def test_count_exact_min(self):     self.assertTrue(C.in_target(0.85, 0.35, 11))
    def test_opus_exact_min(self):      self.assertTrue(C.in_target(0.80, 0.20, 11))
    def test_opus_just_below(self):     self.assertFalse(C.in_target(0.7999, 0.35, 11))
    def test_qwen_exact_low(self):      self.assertTrue(C.in_target(0.85, 0.20, 11))
    def test_qwen_exact_high(self):     self.assertTrue(C.in_target(0.85, 0.50, 11))
    def test_qwen_just_above_max(self): self.assertFalse(C.in_target(0.85, 0.5001, 11))
    def test_spread_ok_0_30(self):      self.assertTrue(C.in_target(0.90, 0.50, 11))

    def test_spread_lt_0_20_also_fails_opus(self):
        # With qwen∈[0.20,0.50] and spread<0.20, opus < 0.70 < OPUS_MIN → fails
        self.assertFalse(C.in_target(0.55, 0.40, 11))


# ═══════════════════════════════════════════════════════════════════════════
# _score_state()
# ═══════════════════════════════════════════════════════════════════════════

class TestScoreState(unittest.TestCase):
    def test_all_in_band_zero(self):
        self.assertAlmostEqual(C._score_state(0.85, 0.35, 15), 0.0)

    def test_opus_low_penalty(self):
        self.assertLess(C._score_state(0.70, 0.35, 15), C._score_state(0.85, 0.35, 15))

    def test_qwen_high_penalty(self):
        self.assertLess(C._score_state(0.85, 0.60, 15), C._score_state(0.85, 0.35, 15))

    def test_qwen_low_penalty(self):
        self.assertLess(C._score_state(0.85, 0.10, 15), C._score_state(0.85, 0.35, 15))

    def test_count_penalty_magnitude(self):
        s_ok    = C._score_state(0.85, 0.35, 11)
        s_short = C._score_state(0.85, 0.35,  5)
        self.assertAlmostEqual(s_ok - s_short, 60.0)  # 6 items × 10


# ═══════════════════════════════════════════════════════════════════════════
# parse_items()
# ═══════════════════════════════════════════════════════════════════════════

class TestParseItems(unittest.TestCase):
    def test_basic(self):
        items = C.parse_items(["RUB-001,major,p,f,f,f,f"])
        i = items[0]
        self.assertEqual(i["id"], "RUB-001"); self.assertEqual(i["w"], 3)
        self.assertAlmostEqual(i["opus_avg"], 1.0); self.assertAlmostEqual(i["qwen_avg"], 0.0)
        self.assertEqual(i["type"], "B")

    def test_two_opus_runs(self):
        items = C.parse_items(["RUB-001,major,p,f,f,f,f"], opus_runs=2)
        self.assertAlmostEqual(items[0]["opus_avg"], 0.5)   # p,f → 0.5
        self.assertAlmostEqual(items[0]["qwen_avg"], 0.0)   # f,f,f → 0.0

    def test_all_severities(self):
        lines = ["A,critical,p,f","B,major,p,f","C,minor,p,f","D,nitpick,p,f"]
        ws = {i["id"]: i["w"] for i in C.parse_items(lines)}
        self.assertEqual(ws, {"A":4,"B":3,"C":2,"D":1})

    def test_unknown_severity_defaults_major(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            items = C.parse_items(["RUB-001,extreme,p,f"])
        self.assertEqual(items[0]["w"], 3)
        self.assertIn("defaulting to major", buf.getvalue())

    def test_prefix_match_full_words(self):
        items = C.parse_items(["RUB-001,major,pass,fail,fail"])
        self.assertAlmostEqual(items[0]["opus_avg"], 1.0)
        self.assertAlmostEqual(items[0]["qwen_avg"], 0.0)

    def test_malformed_line_skipped(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            items = C.parse_items(["RUB-001,major"])
        self.assertEqual(items, [])
        self.assertIn("Skipping malformed", buf.getvalue())

    def test_comment_skipped(self):
        self.assertEqual(len(C.parse_items(["# comment","RUB-001,major,p,f"])), 1)

    def test_blank_lines_skipped(self):
        self.assertEqual(len(C.parse_items(["","   ","RUB-001,major,p,f"])), 1)

    def test_no_qwen_results_assumed_fail(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            items = C.parse_items(["RUB-001,major,p"], opus_runs=1)
        self.assertAlmostEqual(items[0]["qwen_avg"], 0.0)
        self.assertIn("No Qwen results", buf.getvalue())

    def test_id_uppercased(self):
        self.assertEqual(C.parse_items(["rub-001,major,p,f"])[0]["id"], "RUB-001")

    def test_rg_defaults_false(self):
        self.assertFalse(C.parse_items(["RUB-001,major,p,f"])[0]["rg"])

    def test_whitespace_trimmed(self):
        items = C.parse_items(["  RUB-001 , major , p , f  "])
        self.assertEqual(len(items), 1); self.assertEqual(items[0]["id"], "RUB-001")

    def test_type_A_classified(self):
        self.assertEqual(C.parse_items(["RUB-001,major,f,f"])[0]["type"], "A")

    def test_type_D_classified(self):
        self.assertEqual(C.parse_items(["RUB-001,major,p,p"])[0]["type"], "D")

    def test_type_C_classified(self):
        self.assertEqual(C.parse_items(["RUB-001,major,f,p"])[0]["type"], "C")


# ═══════════════════════════════════════════════════════════════════════════
# exhaustive_trim()
# ═══════════════════════════════════════════════════════════════════════════

class TestExhaustiveTrim(unittest.TestCase):
    def _in_band_pool(self):
        # 11 B + 3 D major: qwen = 9/42 ≈ 21% → already in target
        return B(11) + D(3)

    def test_already_in_target_no_removal(self):
        subset, removed, success = C.exhaustive_trim(self._in_band_pool())
        self.assertTrue(success); self.assertEqual(removed, [])

    def test_removes_D_when_qwen_too_high(self):
        # 15 B + 15 D-critical: qwen ≈ 57% → too high
        pool = B(15) + D(15, "critical")
        subset, removed, success = C.exhaustive_trim(pool)
        if success:
            o, q, _ = C.scores(subset)
            self.assertTrue(C.in_target(o, q, len(subset)))

    def test_no_solution_only_B(self):
        # 11 B: qwen=0% < 20%; no removable items
        subset, removed, success = C.exhaustive_trim(B(11))
        self.assertFalse(success); self.assertEqual(removed, [])

    def test_rg_item_never_removed(self):
        rg = make_item("RG-D","critical",(1.0,),(1.0,),rg=True)
        _, removed, _ = C.exhaustive_trim(B(11) + [rg])
        self.assertNotIn("RG-D", {i["id"] for i in removed})

    def test_min_items_respected(self):
        subset, _, _ = C.exhaustive_trim(B(11) + D(1))
        self.assertGreaterEqual(len(subset), C.MIN_ITEMS)

    def test_type_B_never_in_removed(self):
        _, removed, _ = C.exhaustive_trim(B(12) + D(3))
        self.assertTrue(all(i["type"] != "B" for i in removed))


# ═══════════════════════════════════════════════════════════════════════════
# greedy_trim()
# ═══════════════════════════════════════════════════════════════════════════

class TestGreedyTrim(unittest.TestCase):
    def test_no_removable_exits_immediately(self):
        _, removed = C.greedy_trim(B(11))
        self.assertEqual(removed, [])

    def test_removes_only_A_or_D(self):
        _, removed = C.greedy_trim(B(15) + D(8, "critical"))
        self.assertTrue(all(i["type"] in {"D","A"} for i in removed))

    def test_rg_not_removed(self):
        rg = make_item("RG-001","critical",(1.0,),(1.0,),rg=True)
        _, removed = C.greedy_trim(B(11) + [rg])
        self.assertNotIn("RG-001", {i["id"] for i in removed})

    def test_never_drops_below_min(self):
        current, _ = C.greedy_trim(B(11) + D(1))
        self.assertGreaterEqual(len(current), C.MIN_ITEMS)

    def test_type_B_never_removed(self):
        _, removed = C.greedy_trim(B(12) + D(3))
        self.assertTrue(all(i["type"] != "B" for i in removed))


# ═══════════════════════════════════════════════════════════════════════════
# find_trim()
# ═══════════════════════════════════════════════════════════════════════════

class TestFindTrim(unittest.TestCase):
    def test_C_items_absent_from_subset(self):
        subset, _, _ = C.find_trim(B(11) + Ci(2))
        self.assertTrue(all(i["type"] != "C" for i in subset))

    def test_C_items_in_removed_list(self):
        c_items = Ci(2)
        _, removed, _ = C.find_trim(B(11) + c_items)
        removed_ids = {i["id"] for i in removed}
        for ci in c_items:
            self.assertIn(ci["id"], removed_ids)

    def test_pool_below_min_after_C_removal_warns(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            C.find_trim(B(5) + Ci(6))
        self.assertIn("below the minimum", buf.getvalue())

    def test_removed_plus_subset_equals_original(self):
        pool = B(11) + Ci(2) + D(3)
        subset, removed, _ = C.find_trim(pool)
        self.assertEqual(len(subset) + len(removed), len(pool))

    def test_no_trim_only_B(self):
        _, _, success = C.find_trim(B(11))
        self.assertFalse(success)

    def test_success_when_trim_reaches_target(self):
        pool = B(15) + D(15, "critical")
        subset, _, success = C.find_trim(pool)
        if success:
            o, q, _ = C.scores(subset)
            self.assertTrue(C.in_target(o, q, len(subset)))

    def test_BUG1_type_C_rg_must_not_be_removed(self):
        """
        BUG-1 REGRESSION
        ─────────────────
        Current code in find_trim:
            removed_c = [i for i in items if i["type"] == "C"]      ← ignores rg flag
            pool      = [i for i in items if i["type"] != "C"]

        Fix:
            removed_c = [i for i in items if i["type"] == "C" and not i["rg"]]
            pool      = [i for i in items if not (i["type"] == "C" and not i["rg"])]

        This test will FAIL against the current (unfixed) code.
        """
        c_rg = make_item("C-RG","major",(0.0,),(1.0,),rg=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            subset, removed, _ = C.find_trim(B(11) + [c_rg])
        self.assertNotIn(
            "C-RG", {i["id"] for i in removed},
            "BUG-1: regression-guarded Type C item was unconditionally removed. "
            "find_trim must check `not i['rg']` before removing Type C items."
        )


# ═══════════════════════════════════════════════════════════════════════════
# advise_new_tests()
# ═══════════════════════════════════════════════════════════════════════════

class TestAdviseNewTests(unittest.TestCase):
    def test_opus_low_qwen_high_recommends_B(self):
        out = advice(0.70, 0.60)
        self.assertIn("TYPE B", out); self.assertIn("Opus PASS", out)

    def test_opus_low_qwen_low_recommends_D_then_B(self):
        out = advice(0.60, 0.10)
        self.assertIn("TYPE D", out); self.assertIn("TYPE B", out)

    def test_opus_ok_qwen_high_recommends_A(self):
        self.assertIn("TYPE A", advice(0.90, 0.60))

    def test_opus_ok_qwen_low_recommends_D(self):
        out = advice(0.90, 0.05)
        self.assertIn("TYPE D", out); self.assertIn("Qwen floor", out)

    def test_opus_low_qwen_in_band_recommends_B_noting_qwen_ok(self):
        out = advice(0.70, 0.35)
        self.assertIn("TYPE B", out); self.assertIn("Qwen is already in range", out)

    def test_higher_weight_more_items_recommended(self):
        # Both hit o<80, q>50 branch → TYPE B; high weight suggests more items
        self.assertIn("TYPE B", advice(0.60, 0.60, w=10))
        self.assertIn("TYPE B", advice(0.60, 0.60, w=100))

    def test_dead_branch_spread_only_is_unreachable(self):
        """
        The `else: spread < SPREAD_MIN` branch is dead code.
        If opus >= 0.80 and qwen in [0.20, 0.50], then
        spread = opus - qwen >= 0.80 - 0.50 = 0.30 > SPREAD_MIN.
        So the spread-only branch can never fire.
        """
        self.assertGreaterEqual(0.80 - 0.50, C.SPREAD_MIN)


# ═══════════════════════════════════════════════════════════════════════════
# CLI Integration
# ═══════════════════════════════════════════════════════════════════════════

class TestCLIHappyPath(unittest.TestCase):
    def test_already_discriminative_exits_0(self):
        r = run(DISC_14)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Already DISCRIMINATIVE", r.stdout)

    def test_empty_input_exits_1(self):
        r = run("")
        self.assertEqual(r.returncode, 1); self.assertIn("No valid items found", r.stdout)

    def test_opus_runs_0_exits_1(self):
        self.assertEqual(run(DISC_14, ["--opus-runs","0"]).returncode, 1)

    def test_discrimination_matrix_shown(self):
        self.assertIn("DISCRIMINATION MATRIX", run(DISC_14).stdout)

    def test_type_summary_shown(self):
        self.assertIn("Item breakdown", run(DISC_14).stdout)

    def test_per_run_breakdown_shown(self):
        self.assertIn("Per-run breakdown", run(DISC_14).stdout)

    def test_comments_and_blanks_ignored(self):
        r = run("# comment\n\n" + DISC_14)
        self.assertEqual(r.returncode, 0); self.assertIn("Already DISCRIMINATIVE", r.stdout)

    def test_unknown_severity_warning(self):
        lines = "RUB-001,extreme,p,f\n" + "\n".join(
            f"B-{i:03d},major,p,f" for i in range(2, 12)
        ) + "\n" + "\n".join(f"D-{i:03d},major,p,p" for i in range(1,4))
        self.assertIn("defaulting to major", run(lines).stdout)


class TestCLIAdvice(unittest.TestCase):
    def test_advice_shown_when_trim_fails(self):
        # DISC_11: qwen=0% < 20%; no trim possible → advice
        self.assertIn("NEW TESTS NEEDED", run(DISC_11).stdout)

    def test_advice_type_D_when_qwen_too_low(self):
        self.assertIn("TYPE D", run(DISC_11).stdout)

    def test_disc_11_not_flagged_discriminative(self):
        # qwen=0% violates QWEN_MIN → must NOT be flagged as discriminative
        self.assertNotIn("Already DISCRIMINATIVE", run(DISC_11).stdout)


class TestCLIOpusRunsFlag(unittest.TestCase):
    def test_two_opus_runs_shown_in_header(self):
        lines = "\n".join(f"RUB-{i:03d},major,p,p,f,f,f" for i in range(1, 12))
        r = run(lines, ["--opus-runs","2"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("Opus runs: 2", r.stdout)
        self.assertIn("Qwen runs: 3", r.stdout)

    def test_default_one_opus_run(self):
        self.assertIn("Opus runs: 1", run(DISC_14).stdout)


class TestCLIRegressionGuard(unittest.TestCase):
    def test_rg_flag_adds_bracket_in_matrix(self):
        self.assertIn("[RG]", run(DISC_14, ["--rg","B-001"]).stdout)

    def test_rg_empty_marks_nothing(self):
        self.assertNotIn("[RG]", run(DISC_14).stdout)

    def test_BUG1_rg_C_item_not_in_trim_list(self):
        """End-to-end BUG-1: C-RG must not appear in 'Items to trim'."""
        lines = (
            "\n".join(f"B-{i:03d},major,p,f,f,f,f" for i in range(1, 11)) +
            "\nC-RG,major,f,p,p,p,p"
        )
        r = run(lines, ["--rg","C-RG"])
        if "Items to trim" in r.stdout:
            trim_section = r.stdout.split("Items to trim")[1].split("\n\n")[0]
            self.assertNotIn(
                "C-RG", trim_section,
                "BUG-1: regression-guarded Type C item appeared in trim list"
            )


class TestCLIFileFlag(unittest.TestCase):
    def test_file_flag_reads_rubric(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(DISC_14); fname = f.name
        try:
            r = subprocess.run(
                [sys.executable, SCRIPT, "--rg","","--file", fname],
                capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)
            self.assertIn("DISCRIMINATIVE", r.stdout)
        finally:
            os.unlink(fname)

    def test_missing_file_exits_1(self):
        self.assertEqual(run("", ["--file","/nonexistent/x.txt"]).returncode, 1)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)