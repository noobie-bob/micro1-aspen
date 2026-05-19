# Calibration Findings

Current source-of-truth findings for Aspen calibration work, with latest Go MCP tuning weighted highest, while retaining useful older Flask/FastMCP/Go HTTP lessons.

## Groups

```text
patterns/   success and failure patterns, including MCP unit-test framing
project/    app structure, project layout, and next-session bootstrap
rubrics/    rubric design, type system, and task mix guidance
archive/    older cross-language examples retained as reference, not active instructions
```

## Core memory

Go remains the strongest substrate, but Go MCP calibrates well only when tests are framed as simple unit tests using `NewServer()` and `CallTool(...)`, with serialized response assertions and short rubric descriptions.
