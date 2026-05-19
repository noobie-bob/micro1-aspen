# Success Patterns

## Strong app patterns

- Go language.
- Small, flat source tree.
- Seeded actors and resources.
- Stable alpha/beta boundary pair.
- Sentinel markers in privileged fields.
- Centralized access checks.
- Centralized or obvious response shaping.
- Direct tool-call test helper.

## Strong rubric patterns

- Short descriptions.
- One-line task-importance justifications.
- Serialized response checks.
- Positive control paired with negative check.
- Sentinels for content absence or presence.
- Stable seeded IDs where exactness matters.

## Strong Type B areas

- non-admin redaction with admin control,
- public comment visible and internal marker absent,
- shell-like input produces no execution marker and benign target works,
- internal URL does not return protected payload and public URL works,
- unsafe formatter name rejected and safe formatter accepted,
- diagnostic or credential non-leak with explicit secret absence,
- malformed/error responses sanitized for stack/path/runtime leakage,
- same-team/admin anti-overblock checks when short and direct.

## MCP unit-test framing success

Go MCP became tractable when the prompt made the testing style explicit:

```text
Use NewServer()
Use CallTool(...)
Serialize the result or error
Assert on the serialized response
```

This matched what models naturally do well:

- initialize object,
- call one tool,
- inspect returned value,
- assert one field, marker, or error,
- add one small positive control.

For MCP, use simple unit tests for floor and product behavior. Use short content-level security checks for Type B.
