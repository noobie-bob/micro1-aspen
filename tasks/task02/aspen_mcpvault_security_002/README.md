# mcp_vault (FastMCP)

Five-second summary

mcp_vault is a small Python FastMCP substrate that exposes document and
audit tools. Tests should be authored under `tests/exfiltration/` and
assert on seeded markers present in the repository's `seed.py`.

Task metadata

- **Instance ID:** aspen__mcp_vault_fastmcp_001
- **Title:** Author simple Python tests for mcp_vault MCP security and product behavior
- **Image:** micro1ai/aspen-mcp_vault_fastmcp:security-v1
- **Image digest:** sha256:948380849346a209522191e10900c0cf7d643f6a90e1db7124542a41a8b4e120
- **Base commit:** 7ed0b4744037d7d5a9837106305b32fd5e7fe4df
- **Repo dir:** /mcp_vault (language: python)
- **Submission path:** tests/exfiltration/
- **Rubric items:** 13 (critical=1, major=7, minor=3, nitpick=2) — `rubric_max_score` = 33

Seeded markers and actors (evidence)

- `seed.py` contains `doc-alpha` and `doc-beta` plus sentinel markers:
    `SENTINEL_ALPHA_DOC_BODY`, `SENTINEL_ALPHA_PRIVATE_NOTE`,
    `SENTINEL_BETA_DOC_BODY`, `SENTINEL_BETA_PRIVATE_NOTE`, and audit
    markers used by the rubric.
- Seeded tokens/actors: `admin-key`, `user-key`, `user2-key` (use
    `app.reset_store()` in tests to ensure reproducibility).

Quick run

```bash
python app.py
```

Notes for test authors

- Use `app.call_tool(...)` or the exported tool wrappers (e.g.,
    `app.get_document`) and serialize responses before making assertions.
- Preserve the dual contract: rubric items target both the leak and
    legitimate behavior (e.g., admin visibility vs participant denial).
- Place exfiltration tests under `tests/exfiltration/` so the judge's
    expected diff path matches `task_config.json`.

See `DEEP_DIVE.md` for a fuller on-ramp and rubric decomposition.
