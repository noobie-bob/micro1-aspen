# Deep Dive: ProjectHub Visibility Benchmark

ProjectHub models a small internal project management service. Users are either an administrator or a participant assigned to a team. Projects belong to teams, tasks belong to projects, and participants are expected to operate only inside their own team. Admin users have broader visibility and may see internal metrics, budget data, and reviewer-only task fields.

The existing smoke tests are intentionally load-bearing. They use Go's standard `testing` package and `net/http/httptest`, and they show that participants can create projects, create tasks, update task status, add comments, upload attachments, and use export/share/duplicate flows on their own projects. They also show a normal admin report-generation flow. Those legitimate behaviors are part of the contract and should continue to pass after security tests are added.

The challenge is to write tests that identify unsafe behavior without overblocking legitimate use. Strong submissions use the seeded team-A/team-B data, exercise the API as both admin and participant users, and inspect response bodies rather than relying on status codes alone. Sensitive marker strings such as `SENTINEL_REVIEWER_NOTES_A`, `SENTINEL_INTERNAL_METRICS_A`, `SENTINEL_ADMIN_CONFIG_A`, and `SENTINEL_INTERNAL_COMMENT` are intentionally present so tests can prove that non-admin responses do not leak privileged content.

This revision narrows the original inflated mock into a compact varied rubric. Instead of scoring many neighboring endpoints separately, it groups related surfaces into richer obligations: project-surface isolation, task-surface isolation, alternate serialization redaction, operational-surface hardening, and realistic workflow-preservation guards. The goal is better discrimination, not a bigger item count.

High-quality submissions should therefore cover three styles of behavior: negative security checks, positive anti-regression checks, and content-level leak checks. A cross-team request should fail, a same-team request should still succeed, and any participant-visible JSON body should be inspected for privileged markers instead of only checking the status line.

The service is written in Go using only the standard library. Do not modify service code for the benchmark; add Go tests under `projecthub/` next to `smoke_test.go` using the existing helper style.

Packaging note: the final agent-facing image should ship only `main.go` and the smoke test. The richer local security suite used for rubric design and calibration should stay outside the copied starter image so the task does not leak its own answer key.
