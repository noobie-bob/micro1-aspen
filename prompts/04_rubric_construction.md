# Realm Aspen: Rubric Construction

## Core Principles

**Atomic & Binary:** Each rubric item must be a simple MET/UNMET check on the agent's diff (no multi-part interpretation). Items may contain multiple linked ideas ("the test exercises the target scenario AND asserts the specific observable behavior") as long as the LLM judge can decide MET vs. UNMET cleanly.

**Scenario-driven, not response-derived:** Criteria stem from the target scenario and the legitimate-flow surface, not from any specific agent's output. An agent producing a fluent-sounding test suite does not automatically satisfy a rubric item.

**Evidence-anchored:** Each rubric description must be specific enough for a human peer reviewer to audit the LLM judge's MET/UNMET call by reading the agent's diff.

**Behaviourally abstract:** The agent reads `task_config.json`. Rubric descriptions must describe the *observable behaviour* the test should verify — NOT the specific fields, endpoints, mechanisms, or attack payloads involved. This is the single most important anti-leakage constraint (see the dedicated section below).

**Stress-tested:** Mentally run the rubric against (a) an agent that asserts as little as possible (only that calls return 200) and (b) an agent that over-asserts (locks down everything, including legitimate flows). Both should fail at least one rubric item.

**Varied, not repetitive:** A strong Aspen rubric does not consist of many near-clones. Spread items across different retrieval paths, serialization shapes, roles, mutation/read-back pairs, and regression flows so smaller models cannot score well by copying one pattern repeatedly.

**Sized for signal:** Use count as a consequence of scenario richness, not as a target to hit mechanically. 11-28 items is typical. Below that range is acceptable only if each item is dense and discriminative. Above that range is acceptable only if the additional items represent genuinely different behaviors.

## Rubric Item Anatomy

Each entry in `ground_truth_issues[]` has four fields:

```json
{
  "id": "RUB-001",
  "severity": "critical",
  "category": "access_control",
  "description": "A test verifies that a participant can only enumerate resources scoped to their own organisational boundary — cross-boundary resources must be absent from list responses. The assertion is structural: it checks resource membership, not just HTTP status."
}
```

The description is the LLM judge's prompt. Write it as a precise behavioural specification — what role, what observable outcome, what the test must assert. But do NOT name specific fields, endpoints, or vulnerability mechanisms.

## Writing Behaviourally Abstract Descriptions (CRITICAL)

The agent sees `task_config.json`, including all rubric descriptions. If descriptions contain specific field names, endpoint paths, or attack payloads, they become a free answer key that non-frontier models can exploit.

### What to avoid

| Leaky element | Example of leakage | Why it's bad |
|---|---|---|
| Field names | "internal_priority, reviewer_notes" | Agent searches for these strings and writes tests targeting them |
| Endpoint paths | "GET /debug/users, POST /tasks/{id}/notify-webhook" | Agent hits these endpoints directly without reasoning |
| Attack payloads | "UNION SELECT, `; echo MARKER`" | Agent copies the payload verbatim |
| Vulnerability labels | "SQL injection in search", "SSRF via webhook" | Agent knows exactly what class to test for |
| Sentinel values | "P0-TOP-SECRET, SENTINEL_METRICS" | Agent looks for these specific markers |

### How to write abstract descriptions

| Concrete (leaky) ❌ | Abstract (correct) ✅ |
|---|---|
| "A test asserts GET /projects returns only projects where team_id matches the caller's team" | "A test verifies that a participant can only enumerate resources scoped to their own organisational boundary" |
| "A test injects `'; UNION SELECT internal_priority FROM tasks --` into the search query" | "A test verifies that the search subsystem does not return data outside the caller's authorised scope, even when the query is crafted to exploit the underlying query engine" |
| "A test asserts that /debug/users returns 401 or 403 for unauthenticated callers" | "A test verifies that diagnostic or troubleshooting endpoints intended for operators are not accessible to unauthenticated callers" |
| "A test asserts that PATCH /tasks/{id} with internal_priority=P0 is rejected for non-admin callers" | "A test verifies that privileged administrative metadata on work items cannot be overwritten by a participant-level caller through the standard update interface" |

### The litmus test

Read each description and ask: "Could a model write a passing test for this item by copying the description alone, without reading the source code?" If yes, the description leaks too much.

## Going Beyond Surface Assertions

The strongest test-quality items go beyond status-code or shallow assertions. The technique varies by scenario:

- **Security scenarios:** Seed sentinel marker bytes (e.g., random tokens) into private artifacts during fixture setup, then assert those marker bytes do not appear anywhere in non-admin responses, including inside zip-archive contents. Catches fixes that return 200 with redacted JSON but leave the bytes reachable through a different serialization path.
- **Feature-coverage scenarios:** Assert on observable side effects (DB state, emitted events, downstream calls) — not just that the API returned 200. Catches implementations that look right at the surface but fail to actually do the work.
- **Regression scenarios:** Assert on the specific characteristic of the bug's incorrect state, not just absence-of-error. A regression test that only checks "no exception was thrown" passes against many alternative buggy states.

## Multi-Step and Consolidated Test Requirements

Tests that require multi-step reasoning (setup → action → verify → cross-check) are significantly more discriminative than single-assertion tests. Design rubric items that require:

- **All-or-nothing coverage:** Instead of one test per field (easy to partially pass), use one test that checks ALL vulnerable fields — the agent must discover the complete set to pass.
- **Loop-based attack vectors:** Instead of testing one injection payload, test multiple attack vectors in a loop — the agent must understand the vulnerability class, not just copy one example.
- **Mutation + read-back:** PATCH a field, then GET to verify it was rejected — not just checking the PATCH response status.
- **Cross-resource verification:** Seed data in resource A, verify it doesn't leak through resource B's endpoint.

### Example: Consolidating near-duplicate tests

**Before (easy for non-frontier models — 7 separate tests):**
```python
def test_patch_task_rejects_internal_priority(): ...
def test_patch_task_rejects_reviewer_notes(): ...
def test_patch_task_rejects_admin_config(): ...
def test_patch_project_rejects_internal_metrics(): ...
def test_patch_project_rejects_budget_allocation(): ...
def test_patch_project_rejects_admin_config(): ...
def test_patch_project_rejects_risk_score(): ...
```

**After (requires comprehensive understanding — 2 consolidated tests):**
```python
def test_patch_task_rejects_mass_assignment():
    """All privileged fields must be rejected in a single PATCH."""
    # Seeds all admin-only fields, patches them as non-admin, verifies ALL unchanged
    
def test_patch_project_rejects_mass_assignment():
    """All privileged project metadata must be rejected in a single PATCH."""
    # Same pattern for project-level fields
```

The consolidated version requires the agent to discover ALL vulnerable fields — if it misses one, the test still fails.

## Hard Regression Guards

The best regression guards are not trivial happy-path echoes. They should force the model to preserve legitimate behavior under realistic complexity, for example:

- Same-team access across both list and detail endpoints, not just one
- Allowed write flows followed by read-back verification
- Legitimate bundled/exported responses that must still work while redacting sensitive content
- Admin-only visibility that remains broader than participant visibility
- Action endpoints (duplicate, share, export) that still function after security fixes

If the anti-overblock section is too simple, frontier models saturate and smaller models get too much reward from generic guard tests.

## Count Guidance

Use count as a consequence of scenario richness, not as a target to hit mechanically.

- 11-28 items is a strong default for most Aspen tasks.
- Below that range is acceptable only if each item is dense, clearly discriminative, and non-redundant.
- Above that range is acceptable only if the additional items represent genuinely different behaviors, not easy neighboring-endpoint copies.

If you find yourself adding many simple items just to raise the score, stop and make the existing items more varied instead.

## Prompt Leakage Constraints

Hard rubric items must come from the substrate, not from hints in `prompt.txt` or `task_config.json`. Avoid:

- Prompts that list the exact endpoints, modules, or route families worth auditing
- Prompts that enumerate bug classes in the same order as the rubric
- Prompts that tell the agent which files to inspect beyond the test directory
- Rubric descriptions that name specific fields, payloads, or endpoint paths
- Referencing `test_smoke.py` in the prompt (it doesn't exist in the production image — reference `conftest.py` instead)

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
