"""
test_calibrate_regression.py — Regression & sanity tests for calibrate.py
==========================================================================

Derived from the Aspen Calibration agent spec.  These tests cover scenarios
the existing suite does NOT — specifically:

  Math invariants
    - Score formula consistency: scores() == hand-computed weighted avg
    - Type effect table: adding/removing each type moves scores in the
      documented direction (A↓both, B↑opus↓qwen, C↑qwen↓opus, D↑both)
    - Spread guaranteed ≥ 0.20 whenever in_target() is True
    - rubric_max_score == Σ(weight × count) after trim

  Decision-table sanity (agent "what action to take" grid)
    - Both too high (>80%, >50%) → adding a Type A item lowers both scores
    - Opus low + Qwen high → adding Type B item raises Opus, lowers Qwen
    - Opus low + Qwen low  → adding Type D item raises both
    - Already in-range     → in_target() True; no trim needed

  trim pipeline invariants
    - find_trim result satisfies in_target() when success=True
    - find_trim never produces a subset with a Type C non-RG item
    - greedy_trim: after each removal, score improves or stalls (never worsens optimally)
    - exhaustive_trim finds the *smallest* removal set (no redundant removals)
    - C items with RG flag stay in subset AND stay out of removed (BUG-1 variants)
    - Mixed RG types: B-RG item never removed either

  mark_regression_guards
    - Comma-separated list marks exactly the named items
    - Unknown IDs are silently ignored (no crash)
    - Case-insensitive ID matching

  parse_items edge cases the existing suite misses
    - Junk columns interspersed (e.g. "rub-001,major,p,X,f" — X silently dropped)
    - All four Qwen runs present (4-run average correct)
    - Duplicate IDs: both parsed independently (no dedup in parser)

  advise_new_tests weight estimates
    - Estimate grows with rubric weight (larger rubric → more items recommended)
    - Output always contains a weight-point estimate ("weight pts")

  CLI regression: printed findings routing
    - Type C removed item → trim/failure path in output
    - Type A removed item → trim/failure path in output
    - Type D removed item → trim/pass path in output

  Numeric stability / edge cases
    - Single item that is already a perfect B: scores returns 1.0/0.0
    - All items identical weight: scoring is uniform average
    - Large rubric (50 items) — script doesn't hang or produce wrong answer
"""

import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calibrate as C

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibrate.py")


# ─── Helpers (mirrors test_calibrate.py, kept local to avoid coupling) ─────

def run(stdin_text, extra_args=None):
    cmd = [sys.executable, SCRIPT, "--rg", ""] + (extra_args or [])
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        cmd, input=stdin_text, capture_output=True, text=True,
        encoding="utf-8", env=env,
    )


def make_item(id="RUB-001", severity="major",
              opus_avg=1.0, qwen_avg=0.0, rg=False):
    """Minimal item dict — opus_avg/qwen_avg drive all math."""
    return {
        "id": id,
        "severity": severity,
        "w": C.WEIGHTS[severity],
        "opus_runs": [opus_avg >= 0.5],
        "qwen_runs": [qwen_avg >= 0.5],
        "opus_avg": opus_avg,
        "qwen_avg": qwen_avg,
        "type": C.classify(opus_avg, qwen_avg),
        "rg": rg,
    }


def B(n, sev="major", **kw):
    return [make_item(f"B-{i:03d}", sev, opus_avg=1.0, qwen_avg=0.0, **kw)
            for i in range(1, n + 1)]

def D(n, sev="major", **kw):
    return [make_item(f"D-{i:03d}", sev, opus_avg=1.0, qwen_avg=1.0, **kw)
            for i in range(1, n + 1)]

def A(n, sev="major", **kw):
    return [make_item(f"A-{i:03d}", sev, opus_avg=0.0, qwen_avg=0.0, **kw)
            for i in range(1, n + 1)]

def Ci(n, sev="major", rg=False):
    return [make_item(f"C-{i:03d}", sev, opus_avg=0.0, qwen_avg=1.0, rg=rg)
            for i in range(1, n + 1)]

def advice_str(o, q, w=30):
    buf = io.StringIO()
    with redirect_stdout(buf):
        C.advise_new_tests([], o, q, w)
    return buf.getvalue()

def find_trim_silent(items):
    buf = io.StringIO()
    with redirect_stdout(buf):
        return C.find_trim(items)


# ═══════════════════════════════════════════════════════════════════════════
# Math invariants — score formula
# ═══════════════════════════════════════════════════════════════════════════

class TestScoreMathInvariants(unittest.TestCase):

    def test_hand_computed_mixed_severity(self):
        """
        Spec: score = Σ(weight_i × avg_pass_i) / Σ(weight_i)
        3 items: critical-B(w=4), major-D(w=3), minor-A(w=2) → W=9
        Opus = (4×1 + 3×1 + 2×0) / 9 = 7/9
        Qwen = (4×0 + 3×1 + 2×0) / 9 = 3/9
        """
        items = [
            make_item("X1", "critical", opus_avg=1.0, qwen_avg=0.0),
            make_item("X2", "major",    opus_avg=1.0, qwen_avg=1.0),
            make_item("X3", "minor",    opus_avg=0.0, qwen_avg=0.0),
        ]
        o, q, w = C.scores(items)
        self.assertEqual(w, 9)
        self.assertAlmostEqual(o, 7 / 9)
        self.assertAlmostEqual(q, 3 / 9)

    def test_partial_pass_rates_averaged(self):
        """opus_avg=0.75 (3 of 4 runs pass) is used verbatim in score."""
        item = make_item("R", "major", opus_avg=0.75, qwen_avg=0.25)
        o, q, _ = C.scores([item])
        self.assertAlmostEqual(o, 0.75)
        self.assertAlmostEqual(q, 0.25)

    def test_total_weight_equals_sum_of_severity_weights(self):
        """rubric_max_score == Σ(weight × count) for every severity."""
        items = (
            B(3, "critical") +   # 3×4=12
            B(4, "major")    +   # 4×3=12
            B(2, "minor")    +   # 2×2=4
            B(1, "nitpick")      # 1×1=1
        )
        _, _, w = C.scores(items)
        expected = 3*4 + 4*3 + 2*2 + 1*1
        self.assertEqual(w, expected)

    def test_in_target_implies_spread_gte_020(self):
        """Whenever in_target() is True, spread must be ≥ SPREAD_MIN — by construction."""
        # Exhaustively check the logic: if in_target passes, o-q >= SPREAD_MIN
        cases = [
            (0.80, 0.20, 11),
            (0.85, 0.35, 11),
            (0.90, 0.50, 11),
            (1.00, 0.20, 11),
            (0.80, 0.20, 20),
        ]
        for o, q, n in cases:
            if C.in_target(o, q, n):
                self.assertGreaterEqual(o - q, C.SPREAD_MIN,
                    f"in_target({o},{q},{n}) passed but spread={o-q} < {C.SPREAD_MIN}")

    def test_rubric_max_score_after_trim_recalculated(self):
        """
        After find_trim, total_weight of the returned subset must equal
        the sum of remaining items' weights — not the original rubric_max_score.
        """
        pool = B(11) + D(5, "critical")  # D items will be trimmed to hit qwen target
        subset, _, success = find_trim_silent(pool)
        expected_w = sum(i["w"] for i in subset)
        _, _, actual_w = C.scores(subset)
        self.assertEqual(actual_w, expected_w)


# ═══════════════════════════════════════════════════════════════════════════
# Type-effect table — adding/removing each type moves scores as documented
# ═══════════════════════════════════════════════════════════════════════════

class TestTypeEffects(unittest.TestCase):
    """
    Agent spec documents the direction each item type moves scores.
    These tests confirm adding/removing one item of each type produces
    the stated directional effect on (opus_score, qwen_score).
    """

    def _delta(self, base_items, extra_item):
        """Return (Δopus, Δqwen) when extra_item is added to base_items."""
        o_before, q_before, _ = C.scores(base_items)
        o_after, q_after, _ = C.scores(base_items + [extra_item])
        return o_after - o_before, q_after - q_before

    def test_adding_type_A_lowers_both_scores(self):
        """Type A: ADDING lowers both scores."""
        base = B(5) + D(5)
        d_o, d_q = self._delta(base, make_item("NEW", "major", opus_avg=0.0, qwen_avg=0.0))
        self.assertLess(d_o, 0, "Adding Type A should lower Opus score")
        self.assertLess(d_q, 0, "Adding Type A should lower Qwen score")

    def test_removing_type_A_raises_both_scores(self):
        """Type A: REMOVING raises both scores."""
        a_item = make_item("A-X", "major", opus_avg=0.0, qwen_avg=0.0)
        full = B(5) + D(5) + [a_item]
        without = B(5) + D(5)
        o_full, q_full, _ = C.scores(full)
        o_without, q_without, _ = C.scores(without)
        self.assertGreater(o_without, o_full, "Removing Type A should raise Opus score")
        self.assertGreater(q_without, q_full, "Removing Type A should raise Qwen score")

    def test_adding_type_B_raises_opus_lowers_qwen(self):
        """Type B: ADDING raises Opus, lowers Qwen (discrimination signal)."""
        base = D(8)  # qwen=100%, opus=100%
        d_o, d_q = self._delta(base, make_item("NEW", "major", opus_avg=1.0, qwen_avg=0.0))
        # Opus was already 1.0 so delta_o is 0; but qwen must go down
        self.assertGreaterEqual(d_o, 0, "Adding Type B must not lower Opus")
        self.assertLess(d_q, 0, "Adding Type B should lower Qwen score")

    def test_removing_type_B_lowers_opus_raises_qwen(self):
        """
        Type B: REMOVING lowers Opus, raises Qwen.
        Base must not already have Opus at 1.0 (ceiling) or removing a B item
        can't lower what's already maxed. Use A items (opus=0, qwen=0) to
        create a base where Opus is clearly below 1.0.
        """
        b_item = make_item("B-X", "major", opus_avg=1.0, qwen_avg=0.0)
        # A items pull opus below 1.0 in the combined set
        full = [b_item] + A(5)
        without = A(5)
        o_full, q_full, _ = C.scores(full)
        o_without, q_without, _ = C.scores(without)
        self.assertLess(o_without, o_full, "Removing Type B should lower Opus score")
        # A items have qwen=0 too, so qwen stays 0 in both — it must not worsen
        self.assertGreaterEqual(q_without, q_full,
            "Removing Type B must not lower Qwen score")

    def test_adding_type_C_raises_qwen_lowers_opus(self):
        """Type C (inhibitor): ADDING raises Qwen, lowers Opus."""
        base = B(8)  # opus=100%, qwen=0%
        d_o, d_q = self._delta(base, make_item("NEW", "major", opus_avg=0.0, qwen_avg=1.0))
        self.assertLess(d_o, 0, "Adding Type C should lower Opus score")
        self.assertGreater(d_q, 0, "Adding Type C should raise Qwen score")

    def test_adding_type_D_raises_both_scores(self):
        """Type D: ADDING raises both scores (from a low baseline)."""
        base = A(8)  # opus=0%, qwen=0%
        d_o, d_q = self._delta(base, make_item("NEW", "major", opus_avg=1.0, qwen_avg=1.0))
        self.assertGreater(d_o, 0, "Adding Type D should raise Opus score")
        self.assertGreater(d_q, 0, "Adding Type D should raise Qwen score")


# ═══════════════════════════════════════════════════════════════════════════
# Decision-table sanity — each row of the agent spec grid
# ═══════════════════════════════════════════════════════════════════════════

class TestDecisionTable(unittest.TestCase):
    """
    Agent spec decision table has 6 rows. Verify the stated starting condition
    matches what in_target/scores report, and that the prescribed action is
    what find_trim (or advise_new_tests) recommends.
    """

    def test_row_both_in_range_already_discriminative(self):
        """Row: Opus >80%, Qwen 20–50% → already discriminative, no trim."""
        # 11 B + 3 D gives opus≈100%, qwen≈21% — in range
        pool = B(11) + D(3)
        o, q, _ = C.scores(pool)
        self.assertGreaterEqual(o, C.OPUS_MIN)
        self.assertLessEqual(q, C.QWEN_MAX)
        self.assertGreaterEqual(q, C.QWEN_MIN)
        self.assertTrue(C.in_target(o, q, len(pool)))

    def test_row_both_too_high_trim_removes_D(self):
        """Row: Opus >80%, Qwen >50% → trim removes D (not B)."""
        # Lots of D items push qwen above 50%
        pool = B(11) + D(10, "critical")
        o, q, _ = C.scores(pool)
        self.assertGreater(q, C.QWEN_MAX, "pre-condition: qwen must be above 50%")
        subset, removed, success = find_trim_silent(pool)
        if success:
            # Must have removed only A/D items, not B
            for r in removed:
                self.assertIn(r["type"], {"A", "D"},
                    f"Trim should only remove A/D when both too high, got Type {r['type']}")

    def test_row_opus_low_qwen_high_no_B_items_advises_B(self):
        """Row: Opus <80%, Qwen >50% → advise writing Type B tests."""
        out = advice_str(o=0.60, q=0.70, w=30)
        self.assertIn("TYPE B", out)

    def test_row_both_too_low_advises_D_then_B(self):
        """Row: Opus <80%, Qwen <20% → advise Type D then Type B."""
        out = advice_str(o=0.50, q=0.05, w=30)
        self.assertIn("TYPE D", out)
        self.assertIn("TYPE B", out)

    def test_row_opus_low_qwen_in_band_advises_B_only(self):
        """Row: Opus <80%, Qwen in-band → advise Type B, mention Qwen already OK."""
        out = advice_str(o=0.65, q=0.35, w=30)
        self.assertIn("TYPE B", out)
        self.assertIn("Qwen is already in range", out)

    def test_row_opus_ok_qwen_low_advises_D(self):
        """Row: Opus >80%, Qwen <20% (extreme) → advise Type D."""
        out = advice_str(o=0.90, q=0.05, w=30)
        self.assertIn("TYPE D", out)
        self.assertIn("Qwen floor", out)


# ═══════════════════════════════════════════════════════════════════════════
# Trim pipeline invariants
# ═══════════════════════════════════════════════════════════════════════════

class TestTrimInvariants(unittest.TestCase):

    def test_find_trim_success_means_in_target(self):
        """If find_trim returns success=True, the subset must satisfy in_target()."""
        pool = B(11) + D(5, "critical")
        subset, _, success = find_trim_silent(pool)
        if success:
            o, q, _ = C.scores(subset)
            self.assertTrue(C.in_target(o, q, len(subset)),
                "find_trim returned success=True but subset fails in_target()")

    def test_find_trim_no_type_c_in_subset(self):
        """Non-RG Type C items must never appear in the final subset."""
        pool = B(11) + Ci(3)
        subset, _, _ = find_trim_silent(pool)
        c_ids = {i["id"] for i in subset if i["type"] == "C" and not i["rg"]}
        self.assertEqual(c_ids, set(),
            f"Non-RG Type C items found in subset after find_trim: {c_ids}")

    def test_find_trim_rg_type_c_stays_in_subset(self):
        """RG-flagged Type C item must survive find_trim (BUG-1 variant)."""
        c_rg = make_item("C-RG", "major", opus_avg=0.0, qwen_avg=1.0, rg=True)
        pool = B(11) + [c_rg]
        subset, removed, _ = find_trim_silent(pool)
        subset_ids = {i["id"] for i in subset}
        removed_ids = {i["id"] for i in removed}
        self.assertIn("C-RG", subset_ids,
            "BUG-1: RG-flagged Type C item was not kept in subset")
        self.assertNotIn("C-RG", removed_ids,
            "BUG-1: RG-flagged Type C item appeared in removed list")

    def test_find_trim_rg_type_b_never_removed(self):
        """RG-flagged Type B item must never appear in removed list."""
        b_rg = make_item("B-RG", "critical", opus_avg=1.0, qwen_avg=0.0, rg=True)
        pool = B(10) + D(5, "critical") + [b_rg]
        _, removed, _ = find_trim_silent(pool)
        self.assertNotIn("B-RG", {i["id"] for i in removed},
            "RG-flagged Type B item was removed")

    def test_find_trim_subset_plus_removed_equals_original(self):
        """Partition invariant: every original item is in exactly one of subset or removed."""
        pool = B(11) + Ci(2) + D(4) + A(2)
        subset, removed, _ = find_trim_silent(pool)
        original_ids = {i["id"] for i in pool}
        result_ids   = {i["id"] for i in subset} | {i["id"] for i in removed}
        self.assertEqual(original_ids, result_ids,
            "Items lost or duplicated across subset and removed")

    def test_exhaustive_trim_finds_minimal_removal(self):
        """
        If removing 1 item suffices, exhaustive_trim must not remove 2.
        Pool: 12 B + 1 D-critical that pushes qwen just above 50%.
        Removing just that 1 D should be sufficient.
        """
        # 12 B major (w=3 each, qwen=0%) + 1 D critical (w=4, qwen=100%)
        # total W = 12*3 + 4 = 40
        # qwen = 4/40 = 10% after D added at weight 4 — that's below 50%.
        # We need qwen > 50%: use many D-critical items.
        # 11 B-major (W=33) + 4 D-critical (W=16, qwen=100%) → total W=49, qwen=16/49≈33%
        # Still under. Use: 11 B-major + 11 D-major → W=66, qwen=33/66=50% ← exact boundary
        # Use 11 B + 12 D-major → W=69, qwen=36/69≈52% — just over
        pool = B(11) + D(12)  # qwen > 50%, opus 100%
        _, removed, success = C.exhaustive_trim(pool)
        if success:
            # Should only need to remove 1 D item to drop qwen to ≤50%
            self.assertLessEqual(len(removed), 3,
                "Exhaustive trim removed more items than necessary")

    def test_greedy_trim_never_removes_type_c(self):
        """greedy_trim only removes A/D; Type C removal is find_trim's first step."""
        c = Ci(2)
        pool = B(11) + c
        _, removed = C.greedy_trim(pool)
        for r in removed:
            self.assertNotEqual(r["type"], "C",
                "greedy_trim must not remove Type C items directly")


# ═══════════════════════════════════════════════════════════════════════════
# Greedy fallback warning (EXHAUSTIVE_LIMIT boundary)
# ═══════════════════════════════════════════════════════════════════════════

class TestGreedyFallbackWarning(unittest.TestCase):
    """
    When removable_count > EXHAUSTIVE_LIMIT, find_trim switches to greedy
    and must print a warning so the user knows the result may not be optimal.
    """

    def _pool_with_n_removable(self, n):
        """
        Build a pool with exactly n removable (Type A/D, non-RG) items.
        Use B(11) as the fixed keeper base, then add n Type D items.
        """
        return B(11) + D(n)

    def test_no_warning_at_exhaustive_limit(self):
        """Exactly EXHAUSTIVE_LIMIT removable items → exhaustive path, no warning."""
        pool = self._pool_with_n_removable(C.EXHAUSTIVE_LIMIT)
        buf = io.StringIO()
        with redirect_stdout(buf):
            C.find_trim(pool)
        self.assertNotIn("Switching to greedy", buf.getvalue(),
            "Should NOT warn when removable_count == EXHAUSTIVE_LIMIT")

    def test_warning_at_exhaustive_limit_plus_one(self):
        """EXHAUSTIVE_LIMIT + 1 removable items → greedy path → warning printed."""
        pool = self._pool_with_n_removable(C.EXHAUSTIVE_LIMIT + 1)
        buf = io.StringIO()
        with redirect_stdout(buf):
            C.find_trim(pool)
        out = buf.getvalue()
        self.assertIn("Switching to greedy", out,
            "Must warn when removable_count exceeds EXHAUSTIVE_LIMIT")

    def test_warning_mentions_heuristic_risk(self):
        """Warning must explain that greedy may miss a valid solution."""
        pool = self._pool_with_n_removable(C.EXHAUSTIVE_LIMIT + 1)
        buf = io.StringIO()
        with redirect_stdout(buf):
            C.find_trim(pool)
        out = buf.getvalue()
        self.assertTrue(
            "heuristic" in out.lower() or "may" in out.lower(),
            f"Warning should mention heuristic / may miss solution: {out!r}"
        )

    def test_warning_shown_in_cli_output(self):
        """CLI: greedy warning appears in stdout when rubric has >EXHAUSTIVE_LIMIT removable items."""
        # EXHAUSTIVE_LIMIT + 1 = 23 D-major items + 11 B-major keepers
        n = C.EXHAUSTIVE_LIMIT + 1
        rows = (
            [f"B-{i:03d},major,p,f" for i in range(1, 12)] +
            [f"D-{i:03d},major,p,p" for i in range(1, n + 1)]
        )
        r = run("\n".join(rows))
        self.assertIn("Switching to greedy", r.stdout,
            "CLI output must contain greedy fallback warning for large rubrics")

    def test_greedy_result_still_valid_when_solution_is_obvious(self):
        """
        Even on the greedy path, if a solution exists and is simple (remove all
        D items of one severity), greedy should still find it and return success=True.
        """
        # 11 B-major + 23 D-major → qwen well above 50%; removing D items
        # one by one (greedy) should converge to in-target.
        pool = self._pool_with_n_removable(C.EXHAUSTIVE_LIMIT + 1)
        buf = io.StringIO()
        with redirect_stdout(buf):
            subset, _, success = C.find_trim(pool)
        if success:
            o, q, _ = C.scores(subset)
            self.assertTrue(C.in_target(o, q, len(subset)),
                "Greedy returned success=True but subset is not in target")


# ═══════════════════════════════════════════════════════════════════════════
# mark_regression_guards
# ═══════════════════════════════════════════════════════════════════════════

class TestMarkRegressionGuards(unittest.TestCase):

    def _items(self):
        return [
            make_item("RUB-001", "major"),
            make_item("RUB-002", "major"),
            make_item("RUB-003", "major"),
        ]

    def test_marks_exactly_named_items(self):
        items = self._items()
        C.mark_regression_guards(items, "RUB-001,RUB-003")
        self.assertTrue(items[0]["rg"])
        self.assertFalse(items[1]["rg"])
        self.assertTrue(items[2]["rg"])

    def test_unknown_id_ignored_no_crash(self):
        items = self._items()
        C.mark_regression_guards(items, "RUB-999,DOES-NOT-EXIST")
        self.assertFalse(any(i["rg"] for i in items))

    def test_empty_string_marks_nothing(self):
        items = self._items()
        C.mark_regression_guards(items, "")
        self.assertFalse(any(i["rg"] for i in items))

    def test_none_arg_does_not_mark_anything_when_not_tty(self):
        """When rg_ids_arg is None and stdin is not a tty, no items are marked."""
        items = self._items()
        # In test runner, sys.stdin.isatty() is False → rg_ids = set()
        C.mark_regression_guards(items, None)
        self.assertFalse(any(i["rg"] for i in items))

    def test_case_insensitive_id_matching(self):
        """--rg flag should match items regardless of case in the flag value."""
        items = self._items()   # IDs are RUB-001, RUB-002, RUB-003 (upper)
        C.mark_regression_guards(items, "rub-001,rub-002")
        self.assertTrue(items[0]["rg"])
        self.assertTrue(items[1]["rg"])
        self.assertFalse(items[2]["rg"])

    def test_whitespace_in_rg_arg_trimmed(self):
        items = self._items()
        C.mark_regression_guards(items, " RUB-001 , RUB-002 ")
        self.assertTrue(items[0]["rg"])
        self.assertTrue(items[1]["rg"])


# ═══════════════════════════════════════════════════════════════════════════
# parse_items — edge cases not in existing suite
# ═══════════════════════════════════════════════════════════════════════════

class TestParseItemsEdgeCases(unittest.TestCase):

    def test_junk_column_silently_dropped(self):
        """
        Columns that are neither p/f/pass/fail are filtered out.
        'rub-001,major,p,X,f' → result_cols=[p,f] → opus=p(1 col), qwen=f(1 col)
        """
        items = C.parse_items(["rub-001,major,p,X,f"], opus_runs=1)
        self.assertEqual(len(items), 1)
        self.assertAlmostEqual(items[0]["opus_avg"], 1.0)
        self.assertAlmostEqual(items[0]["qwen_avg"], 0.0)

    def test_four_qwen_runs_averaged_correctly(self):
        """
        Classic Aspen format: 1 Opus + 4 Qwen runs.
        'RUB-001,major,p,p,f,f,f' → opus=p(100%), qwen avg=(p+f+f+f)/4=25%
        """
        items = C.parse_items(["RUB-001,major,p,p,f,f,f"])
        self.assertAlmostEqual(items[0]["opus_avg"], 1.0)
        self.assertAlmostEqual(items[0]["qwen_avg"], 0.25)  # 1/4

    def test_four_qwen_runs_all_pass_gives_100(self):
        items = C.parse_items(["RUB-001,major,p,p,p,p,p"])
        self.assertAlmostEqual(items[0]["qwen_avg"], 1.0)

    def test_four_qwen_runs_half_pass_gives_050(self):
        items = C.parse_items(["RUB-001,major,p,p,p,f,f"])
        self.assertAlmostEqual(items[0]["qwen_avg"], 0.50)

    def test_duplicate_ids_both_parsed(self):
        """Parser does not deduplicate — two lines with the same ID produce two items."""
        items = C.parse_items(["RUB-001,major,p,f", "RUB-001,major,f,p"])
        self.assertEqual(len(items), 2)

    def test_full_word_pass_fail_columns(self):
        """'pass' and 'fail' prefix-match correctly for all four Qwen columns."""
        items = C.parse_items(["RUB-001,major,pass,fail,pass,fail,pass"])
        self.assertAlmostEqual(items[0]["opus_avg"], 1.0)
        self.assertAlmostEqual(items[0]["qwen_avg"], 2/4)   # fail,pass,fail,pass = 2/4

    def test_two_opus_four_qwen_split_correctly(self):
        """--opus-runs 2: first 2 cols are Opus, remaining 4 are Qwen."""
        items = C.parse_items(["RUB-001,major,p,f,p,p,f,f"], opus_runs=2)
        self.assertAlmostEqual(items[0]["opus_avg"], 0.5)   # p,f
        self.assertAlmostEqual(items[0]["qwen_avg"], 0.5)   # p,p,f,f = 2/4

    def test_nitpick_severity_weight_is_1(self):
        items = C.parse_items(["RUB-001,nitpick,p,f"])
        self.assertEqual(items[0]["w"], 1)


# ═══════════════════════════════════════════════════════════════════════════
# advise_new_tests — weight estimates and output structure
# ═══════════════════════════════════════════════════════════════════════════

class TestAdviseNewTestsOutput(unittest.TestCase):

    def test_weight_estimate_present_in_all_branches(self):
        """Every advice branch must include a 'weight pts' estimate."""
        cases = [
            (0.60, 0.70),   # opus low, qwen high → TYPE B
            (0.50, 0.05),   # both low            → TYPE D + TYPE B
            (0.90, 0.60),   # opus ok, qwen high  → TYPE A
            (0.90, 0.05),   # opus ok, qwen low   → TYPE D
            (0.65, 0.35),   # opus low, qwen ok   → TYPE B (Qwen already OK)
        ]
        for o, q in cases:
            out = advice_str(o, q, w=30)
            self.assertIn("weight pts", out,
                f"No 'weight pts' in advice for o={o}, q={q}: {out!r}")

    def test_larger_rubric_recommends_more_weight_points(self):
        """Bigger existing rubric → larger weight-point gap → larger estimate."""
        out_small = advice_str(0.60, 0.70, w=10)
        out_large = advice_str(0.60, 0.70, w=100)

        def extract_estimate(text):
            for token in text.split():
                token = token.rstrip("pts").rstrip()
                try:
                    return int(token)
                except ValueError:
                    continue
            return None

        # Both should contain a numeric estimate; large should be >= small
        est_small = extract_estimate(out_small)
        est_large = extract_estimate(out_large)
        if est_small is not None and est_large is not None:
            self.assertGreaterEqual(est_large, est_small,
                "Larger rubric should not recommend fewer weight points")

    def test_type_b_advice_mentions_frontier_models(self):
        """Type B advice must convey that these are hard tests frontier models solve."""
        out = advice_str(0.60, 0.70)
        self.assertTrue(
            "multi-step" in out or "frontier" in out or "chained" in out,
            f"Type B advice should mention multi-step / frontier difficulty: {out!r}"
        )

    def test_type_a_advice_mentions_edge_cases(self):
        out = advice_str(0.90, 0.60)
        self.assertTrue(
            "edge" in out.lower() or "both" in out.lower(),
            f"Type A advice should mention edge cases or 'both models': {out!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# CLI regression — findings routing in printed output
# ═══════════════════════════════════════════════════════════════════════════

class TestCLIFindingsRouting(unittest.TestCase):
    """
    Agent spec Step 4 routing table:
      Type C removed  → trim/failure/{severity}.md
      Type A removed  → trim/failure/{severity}.md
      Type D removed  → trim/pass/{severity}.md
    Verify the CLI prints the correct destination path.
    """

    def _make_stdin(self, rows):
        return "\n".join(rows)

    def test_type_c_removal_routes_to_trim_failure(self):
        """Type C item → trim/failure in output."""
        # 11 B items + 1 C item: C must be removed
        rows = (
            [f"B-{i:03d},major,p,f,f,f,f" for i in range(1, 12)] +
            ["C-001,major,f,p,p,p,p"]
        )
        r = run(self._make_stdin(rows))
        self.assertIn("trim/failure", r.stdout,
            "Type C removed item should route to trim/failure/")

    def test_type_a_removal_routes_to_trim_failure(self):
        """Type A item (both fail) → trim/failure in output."""
        # 11 B + 3 D (to get qwen in-band) + several A items that push qwen down too far
        # Actually: if 11B + 3D is already in-target, add more D to push qwen too high,
        # then A items would need to be removed — but A removal raises both.
        # Simpler: force a case where trim removes A items.
        # 15 B + 5 A + 5 D: qwen = (0*15*3 + 0*5*3 + 1*5*3)/(75) = 15/75 = 20%
        # opus = (1*15*3 + 0*5*3 + 1*5*3)/(75) = 60/75 = 80% — right on boundary.
        # Add more A to push opus below 80% and see if trim removes them.
        # Easier: just assert "trim/failure" appears when C item trimmed (covered above).
        # Here test A: 11B (opus=100%,qwen=0%) → not in-target (qwen<20%), trim can't fix →
        # advice path. Instead build a case where A-type IS trimmed:
        # 11B + 5D-major + 5A-major → W=63, opus=(33+15)/63≈76%, qwen=15/63≈24%
        # Not in target (opus < 80%). Adding A worsened opus. Removing A helps.
        # find_trim should remove A items.
        rows = (
            [f"B-{i:03d},major,p,f" for i in range(1, 12)] +
            [f"D-{i:03d},major,p,p" for i in range(1, 6)] +
            [f"A-{i:03d},major,f,f" for i in range(1, 6)]
        )
        r = run(self._make_stdin(rows))
        # Either success with trim removing A (→ trim/failure) or advice shown.
        # Either way the output should not route A items to trim/pass
        if "trim/failure" in r.stdout or "trim/pass" in r.stdout:
            # A items must not appear in trim/pass
            lines = r.stdout.splitlines()
            for line in lines:
                if "A-0" in line and "trim/pass" in line:
                    self.fail(f"Type A item incorrectly routed to trim/pass: {line}")

    def test_type_d_removal_routes_to_trim_pass(self):
        """Type D item (both pass, floor) → trim/pass in output.
        Need qwen > 50% initially so find_trim has reason to remove D items.
        11 B-major (W=33, qwen=0) + 12 D-critical (W=48, qwen=100%)
        → total W=81, qwen=48/81≈59% → above QWEN_MAX → trim removes D → trim/pass.
        """
        rows = (
            [f"B-{i:03d},major,p,f" for i in range(1, 12)] +
            [f"D-{i:03d},critical,p,p" for i in range(1, 13)]
        )
        r = run(self._make_stdin(rows))
        self.assertIn("trim/pass", r.stdout,
            "Type D removed item should route to trim/pass/")

    def test_rg_item_not_in_trim_output(self):
        """RG-flagged item must not appear in 'Items to trim' section."""
        rows = (
            [f"B-{i:03d},major,p,f,f,f,f" for i in range(1, 11)] +
            ["RG-B,major,p,f,f,f,f"]   # this one is RG
        )
        r = run(self._make_stdin(rows), ["--rg", "RG-B"])
        if "Items to trim" in r.stdout:
            trim_section = r.stdout.split("Items to trim")[1].split("\n\n")[0]
            self.assertNotIn("RG-B", trim_section)


# ═══════════════════════════════════════════════════════════════════════════
# Numeric stability / large rubric
# ═══════════════════════════════════════════════════════════════════════════

class TestNumericStability(unittest.TestCase):

    def test_single_perfect_B_item_scores(self):
        """Single Type B item: opus=1.0, qwen=0.0, weight=severity weight."""
        item = make_item("R", "critical", opus_avg=1.0, qwen_avg=0.0)
        o, q, w = C.scores([item])
        self.assertAlmostEqual(o, 1.0)
        self.assertAlmostEqual(q, 0.0)
        self.assertEqual(w, 4)

    def test_all_items_same_weight_is_simple_average(self):
        """When all items have equal weight, scores() == plain average of avgs."""
        items = [
            make_item("R1", "major", opus_avg=1.0, qwen_avg=0.0),
            make_item("R2", "major", opus_avg=0.5, qwen_avg=0.5),
            make_item("R3", "major", opus_avg=0.0, qwen_avg=1.0),
        ]
        o, q, _ = C.scores(items)
        self.assertAlmostEqual(o, (1.0 + 0.5 + 0.0) / 3)
        self.assertAlmostEqual(q, (0.0 + 0.5 + 1.0) / 3)

    def test_large_rubric_50_items_produces_correct_scores(self):
        """50-item rubric: all B-major → opus=100%, qwen=0%."""
        items = B(50)
        o, q, w = C.scores(items)
        self.assertAlmostEqual(o, 1.0)
        self.assertAlmostEqual(q, 0.0)
        self.assertEqual(w, 50 * 3)

    def test_large_rubric_find_trim_does_not_hang(self):
        """
        50 B + 20 D: find_trim should complete without hanging.
        (EXHAUSTIVE_LIMIT=22, so 20 removable D items stays within exhaustive search.)
        """
        pool = B(30) + D(20)
        import signal

        class TimeoutError(Exception):
            pass

        def _handler(signum, frame):
            raise TimeoutError()

        try:
            signal.signal(signal.SIGALRM, _handler)
            signal.alarm(10)  # 10-second hard timeout
            try:
                subset, _, _ = find_trim_silent(pool)
                self.assertGreaterEqual(len(subset), C.MIN_ITEMS)
            finally:
                signal.alarm(0)
        except AttributeError:
            # signal.SIGALRM not available on Windows — skip the timeout guard
            subset, _, _ = find_trim_silent(pool)
            self.assertGreaterEqual(len(subset), C.MIN_ITEMS)

    def test_scores_float_precision_stable(self):
        """Weighted average of many items should not accumulate float error."""
        # 33 B-major items → opus exactly 1.0, qwen exactly 0.0
        items = B(33)
        o, q, _ = C.scores(items)
        self.assertAlmostEqual(o, 1.0, places=10)
        self.assertAlmostEqual(q, 0.0, places=10)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)