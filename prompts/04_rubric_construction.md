# Realm Aspen: Rubric Construction

## Core Principles

**Atomic & Binary:** Each rubric item must be a simple MET/UNMET check on the agent's diff (no multi-part interpretation). Items may contain multiple linked ideas ("the test exercises the target scenario AND asserts the specific observable behavior") as long as the LLM judge can decide MET vs. UNMET cleanly.

**Scenario-driven, not response-derived:** Criteria stem from the target scenario and the legitimate-flow surface, not from any specific agent's output. An agent producing a fluent-sounding test suite does not automatically satisfy a rubric item.

**Evidence-anchored:** Each rubric description must be specific enough for a human peer reviewer to audit the LLM judge's MET/UNMET call by reading the agent's diff.

**Stress-tested:** Mentally run the rubric against (a) an agent that asserts as little as possible (only that calls return 200) and (b) an agent that over-asserts (locks down everything, including legitimate flows). Both should fail at least one rubric item.

**Varied, not repetitive:** A strong Aspen rubric does not consist of many near-clones. Spread items across different retrieval paths, serialization shapes, roles, mutation/read-back pairs, and regression flows so smaller models cannot score well by copying one pattern repeatedly.

**Sized for signal:** A good default is roughly 11-18 substantive rubric items or equally meaningful test obligations. Larger rubrics are fine when the scenario genuinely supports more distinct checks; they are usually a mistake when the extra items are just simple repetitions of the same pattern.

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

## Hard Regression Guards

The best regression guards are not trivial happy-path echoes. They should force the model to preserve legitimate behavior under realistic complexity, for example:

- same-team access across both list and detail endpoints, not just one
- allowed write flows followed by read-back verification
- legitimate bundled/exported responses that must still work while redacting sensitive content
- admin-only visibility that remains broader than participant visibility

If the anti-overblock section is too simple, frontier models saturate and smaller models get too much reward from generic guard tests.

## Count Guidance

Use count as a consequence of scenario richness, not as a target to hit mechanically.

- 11-18 items is a strong default for most Aspen tasks.
- Below that range is acceptable only if each item is dense, clearly discriminative, and non-redundant.
- Above that range is acceptable only if the additional items represent genuinely different behaviors, not easy neighboring-endpoint copies.

If you find yourself adding many simple items just to raise the score, stop and make the existing items more varied instead.

## Prompt Leakage Constraints

Hard rubric items must come from the substrate, not from hints in `prompt.txt`. Avoid prompts that:

- list the exact endpoints, modules, or route families worth auditing
- enumerate bug classes in the same order as the rubric
- tell the agent which files to inspect beyond the legitimate test location and smoke-test reference

The prompt should read like a symptom report from a teammate, not a scavenger hunt.

## Discrimination Ladder Targets

After calibration, rubric items distribute along a ladder. A well-designed rubric should produce roughly:

| Rung | Catch rate | Target proportion |
|---|---|---|
| Frontier-saturated | ≥ 58% | ~30% of items — coverage baseline |
| Mid-tier | 42–58% | ~30% of items — solid threat-model induction |
| Hard rungs | 25–42% | ~25% of items — chained-flow + dual-contract reasoning |
| Top-of-frontier | ≤ 10% | ≥ 1 item — the discrimination signal |

As a task-level target, Opus 4.7 should usually average around 75-85% and Qwen around 20-50%. If Opus is consistently above 95%, the task likely lacks enough hard rungs or regression complexity. If Qwen is consistently above 50%, the scenario is often too repetitive or too explicitly hinted.
