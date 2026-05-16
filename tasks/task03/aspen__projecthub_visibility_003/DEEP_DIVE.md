# Deep Dive: ProjectHub Visibility 003

## Five-Second Summary

ProjectHub is a compact Go HTTP service that manages teams, projects, tasks, comments, attachments, shares, and reporting flows. The scenario is not one isolated endpoint bug: it is a deliberately tangled set of visibility, redaction, share-state, operational-surface, and input-handling problems that all show up as externally observable behavior. That makes this a test-authoring task rather than a bug-fix task.

## Why Test-Authoring Is the Right Shape

The right artifact here is a behavioral test suite because the service exposes the same state through several paths and role combinations. A good suite has to enforce the dual contract: direct coverage that proves participants cannot cross team boundaries or see privileged data, and anti-overblock coverage that proves legitimate same-team, admin, lead, and auditor flows still work after a fix. A patch that simply blocks everything would be wrong, and a test suite that only checks one route family would miss the real scenario.

## What the Agent Sees

The substrate is a small Go module. `projecthub/wire.go` registers the full HTTP surface. `projecthub/common.go` contains most of the authorization, response-shaping, and handler logic. `projecthub/types.go` defines the domain model for users, teams, projects, tasks, comments, attachments, shares, and audit events. `projecthub/paths.go` adds noisy packet, knot, drift, and weave helpers that increase repository reasoning surface without changing the basic external contract. `tests/smoke_test.go` demonstrates the intended happy-path flows for participants, leads, admins, sharing, bundles, search, and reporting.

## What the Scenario Looks Like as Code

The interesting code shape is centralized authorization plus inconsistent view shaping. The project gate and task gate helpers decide access through branches like admin, team, mirror, share, audit, and task-person access. Separate projector functions decide which fields a caller sees. That is realistic engineering territory: once one service tries to support normal product flows, mirrored data, shared access, legacy endpoints, operational tooling, and debug helpers at the same time, scope checks and redaction logic drift apart. Here that shows up in widened list behavior, mutable privileged fields, predictable share tokens, overly trusting attachment and webhook or report paths, and verbose error or debug output.

## How the Rubric Items Decompose the Scenario

The rubric is intentionally merged into denser journeys rather than one tiny endpoint-local check per item. Eight critical items cover the main scenario chains: access-control and anti-overblock behavior, response redaction, stateful sharing, mass assignment with readback, debug and legacy and ops exposure, injection and traversal and SSRF variants, weak token generation, and error exposure. Twenty major items cover narrower but still important scope leaks and positive-role boundaries. Seven minor items cover boundary behavior, controls, and repeatability. Four nitpick items reward sentinel markers, reusable helpers, merged flows, and clear diagnostics.

## How to Read the Calibration Numbers

Start with mean reward and saturation rate, but do not stop there. The per-rubric catch table is the real signal: a good task has some baseline items that strong and mid-tier models can catch, some harder items that only stronger models catch reliably, and at least one frontier-skewed rung. If smaller models catch nearly every critical chain, the rubric is too easy. If frontier models miss the positive-control and anti-overblock items, the issue is often prompt or smoke-surface clarity rather than true task difficulty. Calibration is good when the task separates models by reasoning depth, not by hidden instructions.



