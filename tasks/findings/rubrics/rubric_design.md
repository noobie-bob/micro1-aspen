# Rubric Design Findings

## Keep descriptions short

Descriptions should usually be one or two lines. Long paragraphs make judge matching brittle and make model behavior less predictable.

Good:

```text
Ensure internal comments are hidden while public comments remain visible for user-key.
```

Avoid:

```text
Call one tool with exact input A, serialize response, assert X, call another tool with exact input B, assert Y, then perform readback and compare fields.
```

## Justification style

The `justification` field should be a one-line explanation of why the task matters.

Good:

```text
Prevents command injection while allowing safe usage.
```

Bad:

```text
Loosened after judge feedback showed models used equivalent payloads.
```

## Serialized response wording

For MCP tasks, say:

```text
serialized response
```

not:

```text
raw HTTP body
```

Models often use direct `CallTool(...)` results, so the correct behavior is to marshal the returned value or error to JSON and assert on that string.

## Exact literals

Use exact literals only for seeded sentinels and stable seeded IDs.

Allow classes for everything else:

- any benign ping target,
- any simple arithmetic expression with asserted expected value,
- any path-style dangerous module name,
- any internal-looking URL.

## Active-vs-archive rule

Active rubric guidance should not contain stale rubric-ID-specific instructions. Keep durable patterns active; move historical examples into archive files.
