# Deep Dive: ProjectHub Visibility 003

## Five-Second Summary

ProjectHub is a compact Go HTTP service for teams, projects, tasks, comments, attachments, sharing, reporting, and operational tooling. The scenario is not one isolated handler bug: the same underlying state leaks through boundary checks, response shaping, delegated access, diagnostic surfaces, and crafted-input paths. That makes this a test-authoring task rather than a bug-fix task.

## Why Test-Authoring Is the Right Shape

The right artifact here is a behavioural suite because the service exposes the same objects through several roles and retrieval paths. A strong suite has to enforce the dual contract: direct coverage that proves non-privileged actors cannot cross organisational boundaries or recover privileged content, and anti-overblock coverage that proves legitimate same-team, admin, and role-scoped flows still work after a fix. A patch that simply denies everything would be wrong, and a test suite that checks only one route family would miss the real scenario.

## What the Agent Sees

The agent lands in a small Go module. `projecthub/wire.go` registers the HTTP surface. `projecthub/common.go` contains almost all of the gate logic, projector functions, and handlers. `projecthub/types.go` defines users, teams, projects, tasks, comments, attachments, shares, and audit events. `projecthub/seed.go` populates a fixed set of actors and sentinel-rich records. `projecthub/paths.go` adds extra packet and weave helpers that increase code-reading surface without changing the external contract.

The seeded actors matter because the visibility model is role-based rather than anonymous-versus-authenticated. The service includes an org-wide admin, same-team participant and lead users, a participant from another team, an auditor-style user, and a child-team guest. The smoke suite demonstrates that ordinary same-team project and task work should continue to function even after the security gaps are closed.

## What the Scenario Looks Like as Code

The interesting code shape is centralised authorization plus inconsistent response shaping. One set of helpers decides whether a caller can reach a project or task. Another set decides what fields appear once access is granted. A third set packages the same records into exports, shares, duplicates, snapshots, summaries, and operational views. That is realistic engineering territory: once a service supports delegated access, mirrored data, historical or debug surfaces, and a handful of auxiliary workflows, scope checks and projector rules drift apart.

In ProjectHub, the drift shows up in several ways. Boundary checks can widen under special conditions. Delegated access is stateful and therefore easy to over-grant. Non-privileged updates can alter fields that should be authoritative. The service also includes predictable access tokens, broad diagnostic surfaces, and a recoverer that returns internal-looking error text. None of those problems require source modification to observe; they are all visible from the HTTP boundary.

## How the Rubric Decomposes the Scenario

The rubric is intentionally compact. Instead of one tiny endpoint-local check per issue, it groups the scenario into denser behavioural journeys:

- 5 critical items cover the main chains: organisational boundary enforcement, response shaping across primary and secondary paths, delegated-scope confinement, operational-surface lockdown, and crafted-input abuse.
- 8 major items cover mutation integrity, token quality, special visibility modes, artifact consistency, widened summaries, specialised role boundaries, error sanitisation, and anti-overblock regression guards.
- 1 minor item rewards repeatability and state isolation.
- 1 nitpick item rewards sentinel-based body assertions and reusable helper quality.

That shape keeps the task within the healthier Aspen range while still forcing multi-actor reasoning, readback checks, and comparison across alternate retrieval paths.

## How to Read the Calibration Numbers

Start with mean reward and saturation rate, but do not stop there. The per-rubric catch table is the real signal: a good task has some floor items that multiple strong models can catch, some harder items that only stronger models catch reliably, and at least one frontier-skewed rung. If smaller models clear most of the critical chains, the prompt or rubric is leaking too much. If frontier models miss the anti-overblock or same-team flows, the issue is usually smoke-surface clarity rather than legitimate task difficulty. Calibration is good when the task separates models by reasoning depth, not by hidden instructions.



