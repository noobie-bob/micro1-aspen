# Realm Aspen: Rubric Construction

## Core Principles

**Atomic & Binary:** Each rubric item must be a simple MET/UNMET check on the agent's diff (no multi-part interpretation). Items may contain multiple linked ideas ("the test exercises the target scenario AND asserts the specific observable behavior") as long as the LLM judge can decide MET vs. UNMET cleanly.

**Scenario-driven, not response-derived:** Criteria stem from the target scenario and the legitimate-flow surface, not from any specific agent's output. An agent producing a fluent-sounding test suite does not automatically satisfy a rubric item.

**Evidence-anchored:** Each rubric description must be specific enough for a human peer reviewer to audit the LLM judge's MET/UNMET call by reading the agent's diff.

**Stress-tested:** Mentally run the rubric against (a) an agent that asserts as little as possible (only that calls return 200) and (b) an agent that over-asserts (locks down everything, including legitimate flows). Both should fail at least one rubric item.

## Rubric Item Anatomy

Each entry in `ground_truth_issues[]` has four fields:

```json
{
  "id": "RUB-001",
  "severity": "major",
  "category": "access_control",
  "description": "A test asserts that a non-admin GET /tasks/{id}
                  response does not contain the private
                  sandbox_config fields (gold_patch_b64,
                  task_config_b64, test_patch_b64,
                  hidden_seed_files)."
}
```

(This example is from the gold sample's security scenario; the same structure applies regardless of scenario.)

The description is the LLM judge's prompt. Write it as a precise specification: what endpoint, what role, what assertion. Avoid vague phrasing like "the test should cover X" — say "a test asserts that..."

## Going Beyond Surface Assertions

The strongest test-quality items go beyond status-code or shallow assertions. The technique varies by scenario:

- **Security scenarios:** seed sentinel marker bytes (e.g., random tokens) into private artifacts during fixture setup, then assert those marker bytes do not appear anywhere in non-admin responses, including inside zip-archive contents. Catches fixes that return 200 with redacted JSON but leave the bytes reachable through a different serialization path.
- **Feature-coverage scenarios:** assert on observable side effects (DB state, emitted events, downstream calls) — not just that the API returned 200. Catches implementations that look right at the surface but fail to actually do the work.
- **Regression scenarios:** assert on the specific characteristic of the bug's incorrect state, not just absence-of-error. A regression test that only checks "no exception was thrown" passes against many alternative buggy states.

## Discrimination Ladder Targets

After calibration, rubric items distribute along a ladder. A well-designed rubric should produce roughly:

| Rung | Catch rate | Target proportion |
|---|---|---|
| Frontier-saturated | ≥ 58% | ~30% of items — coverage baseline |
| Mid-tier | 42–58% | ~30% of items — solid threat-model induction |
| Hard rungs | 25–42% | ~25% of items — chained-flow + dual-contract reasoning |
| Top-of-frontier | ≤ 10% | ≥ 1 item — the discrimination signal |
