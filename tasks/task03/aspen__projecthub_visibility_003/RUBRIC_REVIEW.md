# Rubric Overlap Review

The earlier task03 draft behaved like a checklist: too many endpoint-local items, too many category labels that leaked the answer, and too little pressure to write dense multi-step tests. This revision compresses the pack into a smaller set of behavioural journeys so the agent has to reason across actors, state transitions, and alternate retrieval paths.

## Merge Decisions

- Cross-boundary list, detail, mutation, and delete checks are merged into one organisational-boundary journey with same-boundary positive controls.
- Primary-response redaction, internal collaboration leakage, and secondary packaging leaks are merged into one response-shaping journey.
- Shared-access, mirrored-access, replay, and expiry issues are treated as one delegated-scope problem instead of several route-local checks.
- Debug, legacy, replay, cursor, audit, and reporting surfaces are grouped as one operational-surface chain so the suite has to compare privileged and non-privileged roles.
- Search abuse, report abuse, outbound-request abuse, and file-retrieval abuse are grouped into one table-driven unsafe-input chain with benign controls.
- Mutation integrity, token quality, special visibility modes, role-scoped boundaries, and regression guards remain separate supporting items because they reward different kinds of reasoning.

## Expected Test Shape

A strong generated suite should land closer to 6-10 dense tests than 30-40 tiny ones. The best shape is a handful of actor-switching journeys with readback, body inspection, sentinel checks, and explicit anti-overblock coverage, plus a smaller number of focused supporting tests for repeatability and helper quality.
