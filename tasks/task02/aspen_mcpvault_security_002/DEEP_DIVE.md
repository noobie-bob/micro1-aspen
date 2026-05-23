# Deep Dive: mcp_vault (FastMCP)

> Audience: a reader who hasn't seen this repo or our internal
> terminology. This file is the on-ramp: after reading it you should
> understand what an AI agent is being graded on, what the substrate
> contains, which markers drive the rubric, and what to look for when
> authoring tests.

## 1. Five-second summary

Agents are asked to **author a pytest-based exfiltration test suite**
against a small FastMCP substrate (`mcp_vault`). The deliverable is a
git diff under `tests/exfiltration/` that the LLM judge scores against
13 weighted rubric criteria. The suite must both (a) catch seeded
information-leak surfaces and (b) preserve legitimate participant and
admin behavior (the dual contract).

## 2. Why test-authoring is the right shape

- The fix shape is ambiguous in real projects (redact, persist-scrub,
	gate at auth). Tests are unambiguous: they codify the threat model
	without prescribing an implementation.
- The rubric rewards test suites that (1) detect leaks and (2) guard
	against over-eager fixes that remove legitimate functionality.

## 3. The setup — what the agent sees

The agent inspects a compact Python FastMCP substrate rooted at
`/mcp_vault`. The important files are:

- `app.py` — exposes tool wrappers and the `call_tool(name, params)`
	helper used in examples.
- `tools.py` — the implementation of the MCP tools (get_document,
	preview_document, search_documents, export_document, etc.).
- `seed.py` — builds the `Store` and seeds actors, orgs, folders,
	documents, and sentinel markers used by the rubric.
- `models.py` — small dataclasses for Document, Folder, Organization,
	AuditRecord, and the in-memory Store.

Tool surfaces exported via `app` (callable by tests):

- `get_folder`, `get_document`, `create_document`, `preview_document`,
	`search_documents`, `export_document`, `list_audit_records`,
	`fetch_remote_attachment`, `redact_text`, `calculate_storage_cost`,
	`admin_diagnostics`.

The agent should treat `app.call_tool(...)` as the canonical API for
exercise; tests commonly call `app.reset_store()` at the start of each
test to ensure reproducibility.

## 4. Seeded actors, markers, and boundaries (evidence)

- Actors / tokens: `admin-key`, `user-key`, `user2-key`.
- Orgs/folders/docs: `org-alpha`, `org-beta`, `folder-alpha`,
	`folder-beta`, `doc-alpha`, `doc-beta`.
- Sentinel markers in `seed.py`:
	- `SENTINEL_ALPHA_DOC_BODY`
	- `SENTINEL_ALPHA_PRIVATE_NOTE`
	- `SENTINEL_BETA_DOC_BODY`
	- `SENTINEL_BETA_PRIVATE_NOTE`
	- `SENTINEL_AUDIT_SECRET`
	- `SENTINEL_METADATA_TOKEN`

These markers are the canonical evidence tests should assert on (or
assert against absence of), and the rubric justifications in
`task_config.json` are anchored to these seeds.

## 5. Important threat surfaces

- document visibility (participant vs admin)
- preview vs full export behavior
- search boundaries and result leakage
- export/download endpoints and enumeration
- audit/diagnostic surfaces
- utility tools that may return secrets (metadata/diagnostic tokens)

Each surface maps to one or more rubric items (see §6).

## 6. Rubric decomposition (how to think about each item)

High-level: the rubric mixes **read-side leak coverage**, **write-side
laundering chains**, and **anti-overblock regression guards**. Tests
should be concrete (call a tool, serialize the response, assert on a
seeded marker or a 4xx denial) and should preserve legitimate flows for
admin and same-org participants.

Representative mapping (authoritative text lives in `task_config.json`):

- **RUB-001 (critical)** — same-org `get_document` for `doc-alpha`:
	assert returned id/title match the seeded `doc-alpha` and
	`SENTINEL_ALPHA_DOC_BODY` evidence.
- **RUB-002 / RUB-003 (major)** — tool call and search assertions that
	anchor to seeded markers/titles so queries reliably return `doc-alpha`.
- **RUB-004 (major)** — admin `get_document` for `doc-beta` returns
	`doc-beta` and seeded beta markers.
- **RUB-009 / RUB-010 (major)** — participant discovery must *not*
	leak `SENTINEL_BETA_PRIVATE_NOTE`, while admin preview/export still
	surfaces beta identifiers (dual-contract anti-overblock items).
- **RUB-012 / RUB-013 (major)** — cross-org preview/fetch attempts by
	non-admin participants should be denied (4xx) given seeded ownership
	in `seed.py`.

Other rubric items encourage reproducibility, explicit expected values,
and reuse of a small serialization helper across tests to avoid brittle
assertions.

## 7. What to look for when writing tests

- Start tests with `app.reset_store()` to guarantee seeded state.
- Use the seeded tokens: `admin-key` for admin flows and `user-key` /
	`user2-key` for participant flows.
- Serialize `call_tool` responses before asserting (avoid opaque
	object identity comparisons).
- Assert explicitly on seeded IDs and sentinel markers (not broad
	truthiness checks).
- Include anti-overblock guards: tests should assert admin still sees
	full data where appropriate and participants can still call their
	own write endpoints for legitimate flows.
- Prefer small, independent tests that place assertions on a single
	surface (read, search, preview, or export) and create chained tests
	only when exercising laundering scenarios (duplicate → mutate → assert).

Example test snippet

```python
import app

def test_get_doc_alpha_as_user():
		app.reset_store()
		res = app.call_tool("get_document", {"token": "user-key", "document_id": "doc-alpha"})
		data = res  # serialize/normalize if necessary
		assert data.get("id") == "doc-alpha"
		assert "SENTINEL_ALPHA_DOC_BODY" in data.get("title", "")
```

## 8. Weights and scoring

`rubric_max_score` = 33. Severity weights: `critical=4`, `major=3`,
`minor=2`, `nitpick=1`. The platform auto-generates one `nl_assertion`
per `ground_truth_issues[]` entry in `task_config.json` and the judge
scores the agent's submission against those assertions.

## 9. Aspen pipeline gotchas

- `rubric_only: true` — there is no in-sandbox verifier; the LLM judge
	scores the git diff against the rubric entries.
- The `task_config.json` rubric is authoritative: do not invent
	calibration numbers or copy other tasks' sample tables into this task.
- Prompt framing should forbid modifying production code; the agent
	must author tests only (the shipped `prompt.txt` enforces this).

## 10. References

- Seed data: `seed.py`
- API wrappers and tool registry: `app.py` and `tools.py`
- Rubric: `task_config.json`

If you want, I can now update `README.md` to include a short rubric
table excerpt or expand any per-rubric justification in this file.
