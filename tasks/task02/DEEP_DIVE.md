# Deep Dive: mcp_vault (FastMCP)

## Summary

mcp_vault is a Python FastMCP server providing organization-scoped document storage, folder reads, document previews, search, exports, audit, diagnostic, and utility-tool behavior. Tests are expected to exercise public tool-call surfaces via `call_tool(...)` or direct function calls and assert on serialized responses and error shapes.

## Important surfaces

- document visibility
- folder visibility
- document preview readback
- search boundaries
- export denial responses
- audit and diagnostic information surfaces
- utility tool calls

## Seeded actors and boundaries

- Actors: `admin-key`, `user-key`, `user2-key`
- Organizations/folders/documents: `org-alpha`, `org-beta`, `folder-alpha`, `folder-beta`, `doc-alpha`, `doc-beta`

## Sentinel markers

- `SENTINEL_ALPHA_DOC_BODY`
- `SENTINEL_BETA_DOC_BODY`
- `SENTINEL_ALPHA_PRIVATE_NOTE`
- `SENTINEL_BETA_PRIVATE_NOTE`
- `SENTINEL_AUDIT_SECRET`
- `SENTINEL_METADATA_TOKEN`

## Weights and scoring

`rubric_max_score` = 31. Weights: critical=4, major=3, minor=2, nitpick=1.
