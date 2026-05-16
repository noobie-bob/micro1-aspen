# Rubric Overlap Review

The previous rubric shape had many endpoint-local checks that a model could satisfy with one request per issue. This version merges overlapping checks into scenario chains. Each critical item requires multiple actors, at least one state transition or endpoint comparison, and body-level assertions.

## Merge Decisions

- Access-control list/detail/task/mutation/delete checks are merged into RUB-001 so the test must prove both isolation and anti-overblocking in one chain.
- Task redaction, project meta redaction, internal comments, and bundle leaks are merged into RUB-002 because they are all response-shaping consistency issues.
- Share acceptance, share replay, and shared-user cross-project escape are merged into RUB-003 and expanded by RUB-018.
- Project and task mass assignment are merged into RUB-004 and require readback through multiple endpoints.
- Debug, legacy, admin, replay, and cursor surfaces are merged into RUB-005, with narrower checks in RUB-011, RUB-012, RUB-016, and RUB-017.
- Search injection, report command injection, webhook SSRF, and attachment traversal remain distinct categories but are grouped into RUB-006 for table-driven I/O variant coverage.
- Weak token tests are isolated in RUB-007 because they need repeated calls and cross-actor comparisons.
- Information exposure is isolated in RUB-008 because stack/path leakage often requires malformed/error responses rather than normal data endpoints.

## Expected Test Shape

A strong generated suite should have fewer, denser tests: access-control journey, redaction journey, stateful share journey, mutation-readback journey, debug/legacy/admin journey, and I/O attack variant journey. This should reduce duplicate tests while increasing reasoning difficulty.
