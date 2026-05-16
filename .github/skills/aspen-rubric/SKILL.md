---
name: aspen-rubric
description: "Rubric construction rules: atomic/binary items, behaviourally abstract descriptions (no field names/endpoints/payloads), anti-overblock guard requirements, discrimination ladder targets, count guidance (11-28 items), sentinel marker pattern, multi-step consolidation. Load when writing, reviewing, or adjusting ground_truth_issues[]."
user-invocable: false
---

# Realm Aspen: Rubric Construction

## Core Principles

**Atomic & Binary:** Each rubric item must be a simple MET/UNMET check. Items may link multiple ideas ("the test exercises X AND asserts Y") as long as the LLM judge can decide MET vs. UNMET cleanly.

**Scenario-driven, not response-derived:** Criteria stem from the target scenario and the legitimate-flow surface, not from any specific agent's output.

**Evidence-anchored:** Each description must be specific enough for a peer reviewer to audit the LLM judge's MET/UNMET call by reading the agent's diff.

**Behaviourally abstract:** Descriptions must describe *observable behaviour* — NOT specific fields, endpoints, mechanisms, or attack payloads.

**Stress-tested:** Run the rubric mentally against (a) an agent that asserts as little as possible and (b) an agent that over-asserts. Both should fail at least one rubric item.

**Varied, not repetitive:** Spread items across different retrieval paths, serialization shapes, roles, mutation/read-back pairs, and regression flows.

**Sized for signal:** 11-28 items is typical. Below is acceptable only if each item is dense and discriminative. Above only if items represent genuinely different behaviors.

## Rubric Item Anatomy

```json
{
  "id": "RUB-001",
  "severity": "critical",
  "category": "access_control",
  "description": "A test verifies that a participant can only enumerate resources scoped to their own organisational boundary — cross-boundary resources must be absent from list responses. The assertion is structural: it checks resource membership, not just HTTP status."
}
```

## Writing Behaviourally Abstract Descriptions (CRITICAL)

| Concrete (leaky) ❌ | Abstract (correct) ✅ |
|---|---|
| "A test asserts GET /projects returns only projects where team_id matches the caller's team" | "A test verifies that a participant can only enumerate resources scoped to their own organisational boundary" |
| "A test injects `'; UNION SELECT internal_priority FROM tasks --` into search" | "A test verifies that the search subsystem does not return data outside the caller's authorised scope, even when the query is crafted to exploit the underlying query engine" |
| "A test asserts that /debug/users returns 401 for unauthenticated callers" | "A test verifies that diagnostic endpoints intended for operators are not accessible to unauthenticated callers" |
| "A test asserts that PATCH /tasks/{id} with internal_priority=P0 is rejected for non-admin" | "A test verifies that privileged administrative metadata cannot be overwritten by a participant-level caller through the standard update interface" |

## Going Beyond Surface Assertions

- **Security scenarios:** Seed sentinel marker bytes into private artifacts during fixture setup, then assert those markers do not appear anywhere in non-admin responses, including inside zip-archive contents.
- **Feature-coverage scenarios:** Assert on observable side effects (DB state, emitted events) — not just that the API returned 200.
- **Regression scenarios:** Assert on the specific characteristic of the bug's incorrect state, not just absence-of-error.

## Multi-Step and Consolidated Test Requirements

Design rubric items that require:

- **All-or-nothing coverage:** One test that checks ALL vulnerable fields — the agent must discover the complete set to pass.
- **Loop-based attack vectors:** Multiple attack vectors in a loop — the agent must understand the vulnerability class.
- **Mutation + read-back:** PATCH a field, then GET to verify it was rejected.
- **Cross-resource verification:** Seed data in resource A, verify it doesn't leak through resource B's endpoint.

### Example: Consolidating near-duplicate tests

**Before (easy — 7 separate tests):**
```python
def test_patch_task_rejects_internal_priority(): ...
def test_patch_task_rejects_reviewer_notes(): ...
# ...5 more
```

**After (requires comprehensive understanding — 2 consolidated tests):**
```python
def test_patch_task_rejects_mass_assignment():
    """All privileged fields must be rejected in a single PATCH."""
    # Seeds ALL admin-only fields, patches as non-admin, verifies ALL unchanged
```

## Hard Regression Guards

The best regression guards are not trivial happy-path echoes:

- Same-team access across both list AND detail endpoints
- Allowed write flows followed by read-back verification
- Legitimate bundled/exported responses that must still work while redacting sensitive content
- Action endpoints (duplicate, share, export) that still function after security fixes

## Discrimination Ladder Targets

| Rung | Catch rate | Target proportion |
|---|---|---|
| Frontier-saturated | ≥ 58% | ~30% of items |
| Mid-tier | 42–58% | ~30% of items |
| Hard rungs | 25–42% | ~25% of items |
| Top-of-frontier | ≤ 10% | ≥ 1 item |

Opus 4.7 should average ~75-85%. Qwen should stay ~20-50%.

## Prompt Leakage Constraints

Hard rubric items must come from the substrate, not from hints in `prompt.txt` or `task_config.json`. Avoid:

- Prompts that list the exact endpoints, modules, or route families worth auditing
- Prompts that enumerate bug classes in the same order as the rubric
- Rubric descriptions that name specific fields, payloads, or endpoint paths
- Referencing `test_smoke.py` in the prompt (it doesn't exist in the production image — reference `conftest.py`)
