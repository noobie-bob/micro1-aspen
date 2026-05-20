# Deep Dive: mcp_hub

## Summary

mcp_hub is a small Python MCP server with team, project, task, comment, search, diagnostic, and utility-tool behavior. The intended test shape is simple unit testing through `call_tool(...)`, with serialized response assertions.

## Why this shape

The app is intentionally flat and seeded so tests can focus on behavior instead of setup. The most useful checks are short: one tool call plus a content assertion, or one negative check plus a small positive control.

## Important surfaces

- project visibility
- comment visibility
- task search
- command-like ping utility
- budget calculation utility
- formatter loading
- asset fetch
- diagnostic and legacy tools

## Seeded actors

- `admin-key`
- `user-key`
- `user2-key`

## Seeded boundaries

- `team-alpha`
- `team-beta`
- `project-alpha`
- `project-beta`
- `task-alpha`
- `task-beta`

## Sentinel markers

- `SENTINEL_ADMIN_CONFIG_ALPHA`
- `SENTINEL_INTERNAL_METRICS_ALPHA`
- `SENTINEL_INTERNAL_COMMENT_ALPHA`
- `SENTINEL_INTERNAL_METADATA_PAYLOAD`
- `super_secret_legacy_key_123!`
