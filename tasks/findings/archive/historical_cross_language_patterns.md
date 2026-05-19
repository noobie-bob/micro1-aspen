# Historical Cross-Language Patterns

This file retains useful older examples without making them active instructions.

## Go HTTP

Go HTTP ProjectHub-style tasks were strongest when they used:

- seeded state,
- central gate helpers,
- central response/projector functions,
- primary and secondary surfaces,
- admin and same-team regression controls.

Go HTTP can support somewhat longer cross-surface journeys than Go MCP, but still fails if too many invariants are stacked in one rubric.

## Python FastMCP

Python FastMCP produced useful B items when the checks were short and content-level:

- command injection plus benign control,
- eval/code expression plus arithmetic control,
- module loading rejection plus safe control,
- internal fetch non-leak plus public control,
- comment visibility with same-team public control.

However, FastMCP became unstable with multi-hop SSRF, stored prompt injection, broad multi-caller admin checks, and long state chains.

## Python Flask

Flat Flask CRUD APIs were hardest to calibrate. They need Go-style affordances:

- seeded state,
- sentinel markers,
- central auth/view helpers,
- secondary surfaces,
- diagnostic surfaces,
- direct body-level assertions.

Without those, models write broad endpoint tests but miss exact proof chains.
