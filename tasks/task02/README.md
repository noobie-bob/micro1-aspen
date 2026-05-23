# mcp_vault (FastMCP)

mcp_vault is a Python FastMCP server for organizations, folders, documents, previews, search, exports, audit records, diagnostics, and small utility tools. This repository contains a small, seeded substrate intended for writing focused exfiltration-style tests under `tests/exfiltration/`.

## Test surface

Tests can call tools directly through the substrate API:

```python
import app
app.reset_store()
result = app.call_tool("get_document", {
    "token": "user-key",
    "document_id": "doc-alpha",
})
```

Always serialize responses before asserting on sentinel markers or internal fields.

## Run server

```bash
python app.py
```

## Seeded actors

- `admin-key`: admin reviewer
- `user-key`: alpha organization participant
- `user2-key`: beta organization participant

## Submission

Place exfiltration tests in `tests/exfiltration/` so the expected diff path matches the task config.
