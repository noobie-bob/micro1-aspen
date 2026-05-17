#!/usr/bin/env python3
"""
Aspen Calibration Calculator
─────────────────────────────
Given pass/fail data for one Opus run and 1-4 Qwen runs, this tool:
  1. Classifies every rubric item into its type (A/B/C/D)
  2. Shows current scores
  3. Finds whether trimming alone can hit the discrimination targets
  4. If not, tells you exactly what new tests to write

Input format (one item per line, paste then Ctrl-D / type END):
  RUB-001,major,p,f,f,p,f
  └─ ID ─┘└─sev─┘└o┘└─── qwen runs ───┘
  opus:  p = pass, f = fail
  qwen:  p/f for each run (1-4 runs, comma-separated after opus)

Severity weights: critical=4, major=3, minor=2, nitpick=1

Targets:  Opus ≥ 80% (1 run)   Qwen 20-50% (avg of provided runs)
          Spread ≥ 0.20         Minimum 11 items after trim

CLI flags:
  --rg RUB-001,RUB-007   Comma-separated regression_guard IDs (skips interactive prompt)
  --file FILE            Read rubric data from a file instead of stdin
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
    """Return (opus_score, qwen_score, total_weight) for a set of items."""
    W = sum(i["w"] for i in items)
    if W == 0:
        return 0.0, 0.0, 0
    Opus = sum(i["w"] for i in items if i["opus"])
    Qwen = sum(i["w"] * i["qwen"] for i in items)
    return Opus / W, Qwen / W, W


def in_target(o, q, n):
    """All three conditions must hold: scores in band AND enough items."""
    return (
        o >= OPUS_MIN
        and QWEN_MIN <= q <= QWEN_MAX
        and (o - q) >= SPREAD_MIN
        and n >= MIN_ITEMS
    )


def classify(opus: bool, qwen_avg: float) -> str:
    """
    A — both fail      (add: lowers both   | remove: raises both)
    B — Opus✓ Qwen✗   (keep: core signal  | remove: hurts Opus, helps Qwen)
    C — Opus✗ Qwen✓   (inhibitor — always remove first)
    D — both pass      (add: raises both   | remove: lowers both)
    """
    if opus and qwen_avg < 0.5:
        return "B"
    if opus and qwen_avg >= 0.5:
        return "D"
    if not opus and qwen_avg < 0.5:
        return "A"
    return "C"  # not opus and qwen_avg >= 0.5


# ── Input parsing ─────────────────────────────────────────────────────────


def parse_items(lines: list[str]) -> list[dict]:
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

        opus = parts[2].startswith("p")
        qwen_res = [
            p.startswith("p") for p in parts[3:] if p in ("p", "f", "pass", "fail")
        ]
        if not qwen_res:
            print(f"  ⚠ No Qwen results for {rub_id}, assuming fail")
            qwen_res = [False]

        qavg = sum(qwen_res) / len(qwen_res)
        w = WEIGHTS[severity]
        t = classify(opus, qavg)

        items.append(
            {
                "id": rub_id,
                "severity": severity,
                "w": w,
                "opus": opus,
                "qwen": qavg,
                "qwen_runs": qwen_res,
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
        # CLI flag supplied — use it (empty string = no RG items)
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
        # Non-interactive (piped) — skip prompt silently
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
    count_pen = max(0.0, MIN_ITEMS - n) * 10.0  # heavy penalty for under-minimum
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

    # Check if C-removal alone was sufficient
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
    removed_c = [i for i in items if i["type"] == "C"]
    pool = [i for i in items if i["type"] != "C"]

    # ── FIX: guard against C-removal shrinking the pool below the minimum ──
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
        # Classic: Opus too low, Qwen too high → need Type B
        gap_o = OPUS_MIN - o
        # (O + Δw) / (W + Δw) = OPUS_MIN  →  Δw = gap_o * W / (1 - OPUS_MIN)
        need_w = round(gap_o * w / (1 - OPUS_MIN)) + 3
        print("  ► Write TYPE B tests (Opus PASS, Qwen FAIL)")
        print("    These are hard, multi-step tests that only frontier models solve.")
        print(f"    Opus gap: {gap_o:.1%} → need ≈{need_w} weight pts")
        print(f"    ≈ {need_w // 3 + 1} major  or  {need_w // 4 + 1} critical  items\n")

    elif o < OPUS_MIN and q < QWEN_MIN:
        # Both too low → Type D to lift both, then Type B to widen gap
        gap_o = OPUS_MIN - o
        need_w = round(gap_o * w / (1 - OPUS_MIN)) + 3
        print("  ► Write TYPE D tests (both PASS — happy-path / regression-guard)")
        print("    Lifts both models. Then widen gap with Type B tests.")
        print(f"    Opus gap: {gap_o:.1%} → need ≈{need_w} weight pts of Type D")
        print(f"    ≈ {need_w // 3 + 1} major  or  {need_w // 4 + 1} critical  items\n")
        print("  ► Then also write TYPE B tests to separate Opus from Qwen.\n")

    elif o >= OPUS_MIN and q > QWEN_MAX:
        # Opus fine, Qwen too high → Type A to pull Qwen down
        gap_q = q - QWEN_MAX
        # (Q*W) / (W + Δw) = QWEN_MAX  →  Δw = (Q*W - QWEN_MAX*W) / QWEN_MAX = gap_q * W / QWEN_MAX
        need_w = round(gap_q * w / QWEN_MAX) + 3
        print("  ► Write TYPE A tests (both FAIL — hard edge cases both models miss)")
        print("    Pulls Qwen below 50% while keeping Opus above 80%.")
        print(f"    Qwen overshoot: {gap_q:.1%} → need ≈{need_w} weight pts of Type A")
        print(f"    ≈ {need_w // 3 + 1} major  or  {need_w // 4 + 1} critical  items\n")

    elif o >= OPUS_MIN and q < QWEN_MIN:
        # Qwen floor too low → Type D to lift Qwen
        gap_q = QWEN_MIN - q
        # (Q*W + Δw) / (W + Δw) = QWEN_MIN  →  Δw = gap_q * W / (1 - QWEN_MIN)
        need_w = round(gap_q * w / (1 - QWEN_MIN)) + 2
        print("  ► Write TYPE D tests (both PASS) — Qwen floor too low")
        print(f"    Qwen floor gap: {gap_q:.1%} → need ≈{need_w} weight pts of Type D")
        print(f"    ≈ {need_w // 3 + 1} major  or  {need_w // 4 + 1} critical  items\n")

    else:
        spread = o - q
        if spread < SPREAD_MIN:
            gap = SPREAD_MIN - spread
            print(
                f"  ► Spread {spread:.1%} is below 0.20 with {gap=} — write TYPE B tests to widen it.\n"
            )


# ── Display helpers ───────────────────────────────────────────────────────

BAR = "─" * 72


def print_matrix(items: list[dict]) -> None:
    TYPE_LABELS = {
        "A": "❌ Both fail",
        "B": "✅ Discrimination signal",
        "C": "⚠️  Inhibitor — must remove",
        "D": "⚪ Both pass (floor)",
    }
    print(f"\n{BAR}")
    print("  DISCRIMINATION MATRIX")
    print(BAR)
    print(
        f"  {'ID':<12} {'Sev':<10} {'Wt':<4} {'Opus':<7} {'Qwen avg':<10} {'T':<3} Signal"
    )
    print(f"  {'─' * 10} {'─' * 8} {'─' * 4} {'─' * 5} {'─' * 8} {'─' * 3} {'─' * 24}")
    for i in items:
        rg = " [RG]" if i["rg"] else ""
        runs = "/".join("P" if r else "F" for r in i["qwen_runs"])
        print(
            f"  {i['id']:<12} {i['severity']:<10} {i['w']:<4} "
            f"{'PASS' if i['opus'] else 'FAIL':<7} "
            f"{i['qwen']:.0%} ({runs}){'':>2} "
            f"{i['type']:<3} {TYPE_LABELS[i['type']]}{rg}"
        )
    print()


def print_scores(label: str, items: list[dict]) -> None:
    o, q, w = scores(items)
    spread = o - q
    ok = in_target(o, q, len(items))
    print(f"  {label}")
    print(
        f"    Items:            {len(items)}  {'✅' if len(items) >= MIN_ITEMS else '❌'} (min {MIN_ITEMS})"
    )
    print(f"    rubric_max_score: {int(w)}")
    print(
        f"    Opus score:       {o:.1%}  {'✅' if o >= OPUS_MIN else '❌'} (target ≥80%)"
    )
    print(
        f"    Qwen score:       {q:.1%}  {'✅' if QWEN_MIN <= q <= QWEN_MAX else '❌'} (target 20–50%)"
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


# ── Main ──────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Aspen Calibration Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
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
        print("  Paste rubric data below. One item per line.")
        print("  Format: RUB-001,major,p,f,f,p,f")
        print("  Type END on a new line when done.\n")
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
        # Piped / redirected stdin — consume everything
        lines = sys.stdin.read().splitlines()
        lines = [_ for _ in lines if _.strip().upper() != "END"]

    items = parse_items(lines)

    if not items:
        print("\n  No valid items found. Exiting.")
        sys.exit(1)

    mark_regression_guards(items, args.rg)

    # ── Report ─────────────────────────────────────────────────────────────
    print(f"\n{BAR}")
    print(f"  ANALYSIS — {len(items)} items loaded")
    print(BAR)

    print_matrix(items)
    print_type_summary(items)

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
    else:
        o2, q2, w2 = scores(subset)
        print("\n  ❌ TRIMMING ALONE CANNOT REACH TARGETS\n")
        if removed:
            print(f"  Best trim removes {len(removed)} item(s):")
            print_removed(removed)
            print("\n  Best achievable after trim:")
            print_scores("Best after trim:", subset)
        else:
            print("  No beneficial trim found.")

        print(f"\n{BAR}")
        print("  NEW TESTS NEEDED")
        print(BAR)
        advise_new_tests(subset, o2, q2, w2)

    print(f"\n{BAR}")


if __name__ == "__main__":
    main()
