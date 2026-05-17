#!/usr/bin/env python3
"""
Aspen Calibration Calculator
─────────────────────────────
Given pass/fail data for 1-N Opus runs and 1-M Qwen runs, this tool:
  1. Classifies every rubric item into its type (A/B/C/D)
  2. Shows current scores
  3. Finds whether trimming alone can hit the discrimination targets
  4. If not, tells you exactly what new tests to write

Input format (one item per line, paste then Ctrl-D / type END):
  RUB-001,major,p,f,  p,f,f,p,f
  └─ ID ─┘└─sev─┘└─opus runs─┘└─── qwen runs ───┘

  Use --opus-runs N to tell the script how many result columns belong
  to Opus (default 1). The remaining columns are treated as Qwen runs.

  p = pass, f = fail  (prefix match, so "pass"/"fail" also work)

Severity weights: critical=4, major=3, minor=2, nitpick=1

Targets:  Opus ≥ 80% (avg across all Opus runs)
          Qwen 20-50% (avg across all Qwen runs)
          Spread ≥ 0.20
          Minimum 11 items after trim

CLI flags:
  --opus-runs N          Number of result columns that belong to Opus (default 1)
  --rg RUB-001,RUB-007   Comma-separated regression_guard IDs (skips interactive prompt)
  --file FILE            Read rubric data from a file instead of stdin

Examples:
  # Classic: 1 Opus run, 4 Qwen runs (backward-compatible)
  python3 calibrate.py --rg "" << 'EOF'
  RUB-001,major,p,f,f,p,f
  EOF

  # 2 Opus runs, 3 Qwen runs
  python3 calibrate.py --opus-runs 2 --rg "" << 'EOF'
  RUB-001,major,p,p,f,f,p
  RUB-002,critical,p,f,p,f,f
  EOF
"""

import sys
import itertools
import argparse
from collections import Counter

# ── Constants ──────────────────────────────────────────────────────────────
WEIGHTS = {"critical": 4, "major": 3, "minor": 2, "nitpick": 1}
OPUS_MIN = 0.80
QWEN_MIN = 0.20
QWEN_MAX = 0.50
SPREAD_MIN = 0.20
MIN_ITEMS = 11
EXHAUSTIVE_LIMIT = 22  # 2^22 ≈ 4M combinations — cap before going greedy

# ── Core maths ────────────────────────────────────────────────────────────


def scores(items):
    """Return (opus_score, qwen_score, total_weight) for a set of items.

    Both Opus and Qwen are now averaged across their respective runs,
    so the formula is symmetric:
        score = Σ(weight_i × avg_pass_rate_i) / Σ(weight_i)
    """
    W = sum(i["w"] for i in items)
    if W == 0:
        return 0.0, 0.0, 0
    Opus = sum(i["w"] * i["opus_avg"] for i in items)
    Qwen = sum(i["w"] * i["qwen_avg"] for i in items)
    return Opus / W, Qwen / W, W


def in_target(o, q, n):
    """All four conditions must hold: scores in band, spread met, enough items."""
    return (
        o >= OPUS_MIN
        and QWEN_MIN <= q <= QWEN_MAX
        and (o - q) >= SPREAD_MIN
        and n >= MIN_ITEMS
    )


def classify(opus_avg: float, qwen_avg: float) -> str:
    """
    Classify an item by the average pass rate of each model family.

    A — both families mostly fail  (avg < 0.5 for both)
    B — Opus mostly passes, Qwen mostly fails  ← discrimination signal
    C — Opus mostly fails, Qwen mostly passes  ← inhibitor, always remove first
    D — both families mostly pass  (avg ≥ 0.5 for both)

    The 0.5 threshold is intentionally coarse: it cleanly separates
    "model mostly gets this right" from "model mostly gets this wrong"
    regardless of how many runs were collected.
    """
    opus_pass = opus_avg >= 0.5
    qwen_pass = qwen_avg >= 0.5

    if opus_pass and not qwen_pass:
        return "B"
    if opus_pass and qwen_pass:
        return "D"
    if not opus_pass and not qwen_pass:
        return "A"
    return "C"  # not opus_pass and qwen_pass


# ── Input parsing ─────────────────────────────────────────────────────────


def parse_items(lines: list[str], opus_runs: int = 1) -> list[dict]:
    """
    Parse rubric lines.  Column layout:
        ID, severity, <opus_runs result cols>, <remaining result cols = Qwen>

    Each result column is 'p'/'pass' (True) or 'f'/'fail' (False).
    """
    items = []
    for raw in lines:
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = [p.strip().lower() for p in raw.split(",")]
        if len(parts) < 3:
            print(f"  ⚠ Skipping malformed line: {raw}")
            continue

        rub_id = parts[0].upper()
        severity = parts[1]
        if severity not in WEIGHTS:
            print(
                f"  ⚠ Unknown severity '{severity}' for {rub_id}, defaulting to major"
            )
            severity = "major"

        result_cols = [
            p for p in parts[2:] if p in ("p", "f", "pass", "fail")
        ]

        # ── Split result columns into Opus and Qwen buckets ──────────────
        opus_results_raw = result_cols[:opus_runs]
        qwen_results_raw = result_cols[opus_runs:]

        if not opus_results_raw:
            print(f"  ⚠ No Opus results for {rub_id}, assuming fail")
            opus_results_raw = ["f"]
        if not qwen_results_raw:
            print(f"  ⚠ No Qwen results for {rub_id}, assuming fail")
            qwen_results_raw = ["f"]

        opus_res = [r.startswith("p") for r in opus_results_raw]
        qwen_res = [r.startswith("p") for r in qwen_results_raw]

        opus_avg = sum(opus_res) / len(opus_res)
        qwen_avg = sum(qwen_res) / len(qwen_res)

        w = WEIGHTS[severity]
        t = classify(opus_avg, qwen_avg)

        items.append(
            {
                "id": rub_id,
                "severity": severity,
                "w": w,
                # Per-run detail (for display)
                "opus_runs": opus_res,
                "qwen_runs": qwen_res,
                # Averaged values (used in all maths)
                "opus_avg": opus_avg,
                "qwen_avg": qwen_avg,
                "type": t,
                "rg": False,  # set below
            }
        )
    return items


def mark_regression_guards(items: list[dict], rg_ids_arg: str | None) -> None:
    """
    Apply regression_guard flags.
    If --rg was passed on the CLI, use that.
    Otherwise prompt interactively — but only when stdin is a terminal,
    so piped invocations never hang or crash on EOFError.
    """
    if rg_ids_arg is not None:
        rg_ids = {x.strip().upper() for x in rg_ids_arg.split(",") if x.strip()}
    elif sys.stdin.isatty():
        raw = (
            input(
                "\n  Flag regression_guard item IDs (comma-separated, or Enter to skip): "
            )
            .strip()
            .upper()
        )
        rg_ids = {x.strip() for x in raw.split(",") if x.strip()}
    else:
        rg_ids = set()

    for i in items:
        if i["id"] in rg_ids:
            i["rg"] = True


# ── Trim engine ───────────────────────────────────────────────────────────


def _score_state(o, q, n) -> float:
    """
    Scalar goodness — higher = closer to all targets simultaneously.
    Includes item-count penalty so we don't silently drop below MIN_ITEMS.
    """
    o_gap = max(0.0, OPUS_MIN - o)
    q_gap = max(0.0, q - QWEN_MAX) + max(0.0, QWEN_MIN - q)
    spread_gap = max(0.0, SPREAD_MIN - (o - q))
    count_pen = max(0.0, MIN_ITEMS - n) * 10.0
    return -(o_gap + q_gap + spread_gap + count_pen)


def greedy_trim(pool: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Greedy removal of Type A/D items (never B, never regression_guard).
    Stops as soon as in_target() is satisfied (scores + count).
    """
    current = pool[:]
    removed = []
    removable_types = {"A", "D"}

    while True:
        o, q, _ = scores(current)
        if in_target(o, q, len(current)):
            break

        candidates = [
            i for i in current if i["type"] in removable_types and not i["rg"]
        ]
        if not candidates:
            break

        best_item = None
        best_score = float("-inf")

        for item in candidates:
            trial = [x for x in current if x["id"] != item["id"]]
            if len(trial) < MIN_ITEMS:
                continue
            to, tq, _ = scores(trial)
            s = _score_state(to, tq, len(trial))
            if s > best_score:
                best_score = s
                best_item = item

        if best_item is None:
            break

        current.remove(best_item)
        removed.append(best_item)

    return current, removed


def exhaustive_trim(pool: list[dict]) -> tuple[list[dict], list[dict], bool]:
    """
    Exhaustive search over all subsets of removable (Type A/D, non-RG) items.
    Tries smallest removals first.
    """
    removable = [i for i in pool if i["type"] in ("A", "D") and not i["rg"]]
    keepers = [i for i in pool if i["type"] == "B" or i["rg"]]

    o, q, _ = scores(pool)
    if in_target(o, q, len(pool)):
        return pool, [], True

    for n_remove in range(1, len(removable) + 1):
        for combo in itertools.combinations(removable, n_remove):
            removed_ids = {i["id"] for i in combo}
            candidate = keepers + [i for i in removable if i["id"] not in removed_ids]
            if len(candidate) < MIN_ITEMS:
                continue
            o, q, _ = scores(candidate)
            if in_target(o, q, len(candidate)):
                return candidate, list(combo), True

    return pool, [], False


def find_trim(items: list[dict]) -> tuple[list[dict], list[dict], bool]:
    """
    Full trim pipeline:
      1. Remove all Type C (always)
      2. Guard: abort if C-removal alone drops us below MIN_ITEMS
      3. Exhaustive or greedy search on remaining Type A/D
    Returns (final_subset, all_removed_items, success).
    """
    removed_c = [i for i in items if i["type"] == "C" and not i["rg"]]
    pool      = [i for i in items if not (i["type"] == "C" and not i["rg"])]

    if len(pool) < MIN_ITEMS:
        print(
            f"\n  ⚠ WARNING: After removing {len(removed_c)} Type C inhibitor(s), "
            f"only {len(pool)} item(s) remain — below the minimum of {MIN_ITEMS}."
        )
        print("  Cannot trim further. Add new Type B or Type D items to recover.\n")
        o, q, _ = scores(pool)
        return pool, removed_c, in_target(o, q, len(pool))

    removable_count = sum(1 for i in pool if i["type"] in ("A", "D") and not i["rg"])

    if removable_count <= EXHAUSTIVE_LIMIT:
        subset, removed_ad, success = exhaustive_trim(pool)
    else:
        print(
            f"\n  ⚠ WARNING: {removable_count} removable items exceeds the exhaustive "
            f"search limit ({EXHAUSTIVE_LIMIT}). Switching to greedy trim.\n"
            f"  Greedy is a heuristic — it may report 'cannot reach targets' even when\n"
            f"  a valid trim exists. If trim fails, try manually removing Type A/D items\n"
            f"  before re-running, or reduce the rubric to fewer than "
            f"{EXHAUSTIVE_LIMIT + 1} removable items."
        )
        subset, removed_ad = greedy_trim(pool)
        o, q, _ = scores(subset)
        success = in_target(o, q, len(subset))

    return subset, removed_c + removed_ad, success


# ── New-test advisor ──────────────────────────────────────────────────────


def advise_new_tests(
    items_after_trim: list[dict], o: float, q: float, w: float
) -> None:
    """When trimming alone fails, advise what new tests to write."""
    print("\n  What to write:\n")

    if o < OPUS_MIN and q > QWEN_MAX:
        gap_o = OPUS_MIN - o
        need_w = round(gap_o * w / (1 - OPUS_MIN)) + 3
        print("  ► Write TYPE B tests (Opus PASS, Qwen FAIL)")
        print("    These are hard, multi-step tests that only frontier models solve.")
        print(f"    Opus gap: {gap_o:.1%} → need ≈{need_w} weight pts")
        print(f"    ≈ {need_w // 3 + 1} major  or  {need_w // 4 + 1} critical  items\n")

    elif o < OPUS_MIN and q < QWEN_MIN:
        gap_o = OPUS_MIN - o
        need_w = round(gap_o * w / (1 - OPUS_MIN)) + 3
        print("  ► Write TYPE D tests (both PASS — happy-path / regression-guard)")
        print("    Lifts both models. Then widen gap with Type B tests.")
        print(f"    Opus gap: {gap_o:.1%} → need ≈{need_w} weight pts of Type D")
        print(f"    ≈ {need_w // 3 + 1} major  or  {need_w // 4 + 1} critical  items\n")
        print("  ► Then also write TYPE B tests to separate Opus from Qwen.\n")

    elif o >= OPUS_MIN and q > QWEN_MAX:
        gap_q = q - QWEN_MAX
        need_w = round(gap_q * w / QWEN_MAX) + 3
        print("  ► Write TYPE A tests (both FAIL — hard edge cases both models miss)")
        print("    Pulls Qwen below 50% while keeping Opus above 80%.")
        print(f"    Qwen overshoot: {gap_q:.1%} → need ≈{need_w} weight pts of Type A")
        print(f"    ≈ {need_w // 3 + 1} major  or  {need_w // 4 + 1} critical  items\n")

    elif o >= OPUS_MIN and q < QWEN_MIN:
        gap_q = QWEN_MIN - q
        need_w = round(gap_q * w / (1 - QWEN_MIN)) + 2
        print("  ► Write TYPE D tests (both PASS) — Qwen floor too low")
        print(f"    Qwen floor gap: {gap_q:.1%} → need ≈{need_w} weight pts of Type D")
        print(f"    ≈ {need_w // 3 + 1} major  or  {need_w // 4 + 1} critical  items\n")

    elif o < OPUS_MIN and QWEN_MIN <= q <= QWEN_MAX:
        # Qwen already in band — only Opus needs lifting without disturbing Qwen
        gap_o = OPUS_MIN - o
        need_w = round(gap_o * w / (1 - OPUS_MIN)) + 3
        print("  ► Write TYPE B tests (Opus PASS, Qwen FAIL)")
        print("    Qwen is already in range — only Opus needs to rise.")
        print("    Hard multi-step tests that frontier models solve but mid-tier miss.")
        print(f"    Opus gap: {gap_o:.1%} → need ≈{need_w} weight pts")
        print(f"    ≈ {need_w // 3 + 1} major  or  {need_w // 4 + 1} critical  items\n")

    else:
        spread = o - q
        if spread < SPREAD_MIN:
            gap = SPREAD_MIN - spread
            print(
                f"  ► Spread {spread:.1%} is below 0.20 (gap={gap:.1%}) — write TYPE B tests to widen it.\n"
            )


# ── Display helpers ───────────────────────────────────────────────────────

BAR = "─" * 80


def _runs_str(results: list[bool]) -> str:
    """Compact run string, e.g. [P/F/P] for three runs."""
    return "/".join("P" if r else "F" for r in results)


def print_matrix(items: list[dict]) -> None:
    TYPE_LABELS = {
        "A": "❌ Both fail",
        "B": "✅ Discrimination signal",
        "C": "⚠️  Inhibitor — must remove",
        "D": "⚪ Both pass (floor)",
    }
    n_opus = len(items[0]["opus_runs"]) if items else 1
    n_qwen = len(items[0]["qwen_runs"]) if items else 1

    print(f"\n{BAR}")
    print("  DISCRIMINATION MATRIX")
    print(BAR)
    print(
        f"  {'ID':<12} {'Sev':<10} {'Wt':<4} "
        f"{'Opus avg':<9} {'Opus runs':<{n_opus*2+1}} "
        f"{'Qwen avg':<10} {'Qwen runs':<{n_qwen*2+1}} "
        f"{'T':<3} Signal"
    )
    print(f"  {'─'*10} {'─'*8} {'─'*4} {'─'*7} {'─'*(n_opus*2)} {'─'*8} {'─'*(n_qwen*2)} {'─'*3} {'─'*24}")

    for i in items:
        rg = " [RG]" if i["rg"] else ""
        opus_runs_s = _runs_str(i["opus_runs"])
        qwen_runs_s = _runs_str(i["qwen_runs"])
        print(
            f"  {i['id']:<12} {i['severity']:<10} {i['w']:<4} "
            f"{i['opus_avg']:.0%}     {opus_runs_s:<{n_opus*2+1}} "
            f"{i['qwen_avg']:.0%}       {qwen_runs_s:<{n_qwen*2+1}} "
            f"{i['type']:<3} {TYPE_LABELS[i['type']]}{rg}"
        )
    print()


def print_scores(label: str, items: list[dict]) -> None:
    o, q, w = scores(items)
    spread = o - q
    ok = in_target(o, q, len(items))

    n_opus = len(items[0]["opus_runs"]) if items else 1
    n_qwen = len(items[0]["qwen_runs"]) if items else 1

    print(f"  {label}")
    print(
        f"    Items:            {len(items)}  {'✅' if len(items) >= MIN_ITEMS else '❌'} (min {MIN_ITEMS})"
    )
    print(f"    rubric_max_score: {int(w)}")
    print(
        f"    Opus score:       {o:.1%}  {'✅' if o >= OPUS_MIN else '❌'} "
        f"(target ≥80%, avg of {n_opus} run{'s' if n_opus != 1 else ''})"
    )
    print(
        f"    Qwen score:       {q:.1%}  {'✅' if QWEN_MIN <= q <= QWEN_MAX else '❌'} "
        f"(target 20–50%, avg of {n_qwen} run{'s' if n_qwen != 1 else ''})"
    )
    print(
        f"    Spread:           {spread:.1%}  {'✅' if spread >= SPREAD_MIN else '❌'} (target ≥0.20)"
    )
    print(f"    Status:           {'✅ DISCRIMINATIVE' if ok else '❌ NOT YET'}")


def print_type_summary(items: list[dict]) -> None:
    c = Counter(i["type"] for i in items)
    print("\n  Item breakdown:")
    print(
        f"    Type A (both fail):       {c['A']:>3}  — add: lowers both  | remove: raises both"
    )
    print(
        f"    Type B (Opus✓ Qwen✗):    {c['B']:>3}  — discrimination signal, keep always"
    )
    print(
        f"    Type C (Opus✗ Qwen✓):    {c['C']:>3}  — inhibitors, remove first always"
    )
    print(
        f"    Type D (both pass):       {c['D']:>3}  — add: raises both  | remove: lowers both"
    )


def print_removed(removed: list[dict]) -> None:
    if not removed:
        return
    print(f"\n  Items to trim ({len(removed)}):")
    c_items = [i for i in removed if i["type"] == "C"]
    ad_items = [i for i in removed if i["type"] in ("A", "D")]
    for i in c_items:
        print(
            f"    • {i['id']} ({i['severity']}, Type C) → tasks/findings/trim/failure/{i['severity']}.md"
        )
    for i in ad_items:
        dest = "trim/failure" if i["type"] == "A" else "trim/pass"
        print(
            f"    • {i['id']} ({i['severity']}, Type {i['type']}) → tasks/findings/{dest}/{i['severity']}.md"
        )


def print_run_summary(items: list[dict], opus_runs: int) -> None:
    """Show a compact per-run breakdown so users can spot outlier runs quickly."""
    if not items:
        return

    n_qwen = len(items[0]["qwen_runs"])
    W_total = sum(i["w"] for i in items)
    if W_total == 0:
        return

    print(f"\n  Per-run breakdown (weighted):")

    # Opus runs
    for r in range(opus_runs):
        run_score = sum(
            i["w"] for i in items if r < len(i["opus_runs"]) and i["opus_runs"][r]
        ) / W_total
        print(f"    Opus run {r+1}:  {run_score:.1%}")

    # Qwen runs
    for r in range(n_qwen):
        run_score = sum(
            i["w"] for i in items if r < len(i["qwen_runs"]) and i["qwen_runs"][r]
        ) / W_total
        print(f"    Qwen run {r+1}:  {run_score:.1%}")


# ── Main ──────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Aspen Calibration Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--opus-runs",
        type=int,
        default=1,
        metavar="N",
        help="Number of result columns that belong to Opus (default 1). "
        "The remaining result columns are treated as Qwen runs. "
        "Example: --opus-runs 2 means cols 3-4 are Opus, col 5+ are Qwen.",
    )
    parser.add_argument(
        "--rg",
        metavar="IDS",
        default=None,
        help="Comma-separated regression_guard item IDs, e.g. --rg RUB-001,RUB-007. "
        "Pass an empty string to explicitly skip (non-interactive). "
        "Omit entirely to be prompted when stdin is a terminal.",
    )
    parser.add_argument(
        "--file",
        "-f",
        metavar="FILE",
        default=None,
        help="Read rubric data from FILE instead of stdin.",
    )
    args = parser.parse_args()

    if args.opus_runs < 1:
        print("  Error: --opus-runs must be at least 1.")
        sys.exit(1)

    print(__doc__)
    print(BAR)

    # ── Read rubric data ───────────────────────────────────────────────────
    if args.file:
        try:
            with open(args.file) as fh:
                lines = fh.readlines()
        except OSError as e:
            print(f"  Error reading {args.file}: {e}")
            sys.exit(1)
    elif sys.stdin.isatty():
        print(f"  Paste rubric data below. One item per line.")
        print(f"  Format: RUB-001,major,<{args.opus_runs} Opus col(s)>,<Qwen cols...>")
        print(f"  Opus runs expected: {args.opus_runs}  (set with --opus-runs N)")
        print(f"  Type END on a new line when done.\n")
        lines = []
        try:
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
        except EOFError:
            pass
    else:
        lines = sys.stdin.read().splitlines()
        lines = [_ for _ in lines if _.strip().upper() != "END"]

    items = parse_items(lines, opus_runs=args.opus_runs)

    if not items:
        print("\n  No valid items found. Exiting.")
        sys.exit(1)

    # Validate consistency: warn if any item has fewer result columns than expected
    for i in items:
        actual_opus = len(i["opus_runs"])
        if actual_opus < args.opus_runs:
            print(
                f"  ⚠ {i['id']}: only {actual_opus} Opus run(s) found "
                f"(expected {args.opus_runs}) — missing runs treated as fail."
            )

    mark_regression_guards(items, args.rg)

    n_opus = len(items[0]["opus_runs"])
    n_qwen = len(items[0]["qwen_runs"])

    # ── Report ─────────────────────────────────────────────────────────────
    print(f"\n{BAR}")
    print(
        f"  ANALYSIS — {len(items)} items  |  "
        f"Opus runs: {n_opus}  |  Qwen runs: {n_qwen}"
    )
    print(BAR)

    print_matrix(items)
    print_type_summary(items)
    print_run_summary(items, n_opus)

    print(f"\n{BAR}")
    print("  CURRENT STATE")
    print(BAR)
    print_scores("Before any trim:", items)

    o, q, _ = scores(items)
    if in_target(o, q, len(items)):
        print("\n  ✅ Already DISCRIMINATIVE — no calibration needed.")
        sys.exit(0)

    # ── Trim simulation ────────────────────────────────────────────────────
    print(f"\n{BAR}")
    print("  TRIM SIMULATION")
    print(BAR)

    subset, removed, success = find_trim(items)

    if success:
        print("\n  ✅ CALIBRATION ACHIEVABLE BY TRIMMING ALONE\n")
        print_removed(removed)
        print("\n  Projected state after trim:")
        print_scores("After trim:", subset)
        print_run_summary(subset, n_opus)
    else:
        o2, q2, w2 = scores(subset)
        print("\n  ❌ TRIMMING ALONE CANNOT REACH TARGETS\n")
        if removed:
            print(f"  Best trim removes {len(removed)} item(s):")
            print_removed(removed)
            print("\n  Best achievable after trim:")
            print_scores("Best after trim:", subset)
            print_run_summary(subset, n_opus)
        else:
            print("  No beneficial trim found.")

        print(f"\n{BAR}")
        print("  NEW TESTS NEEDED")
        print(BAR)
        advise_new_tests(subset, o2, q2, w2)

    print(f"\n{BAR}")


if __name__ == "__main__":
    main()