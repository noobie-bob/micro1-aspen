# Deep Dive — `aspen_mcpvault_security_002`

> **Audience.** A reader who has not seen this repo or this task before.
> By the end you should be able to say (a) what an AI model is being
> graded on here, (b) what the leak looks like as code, (c) where the
> seeded markers live, and (d) how to interpret the calibration
> scaffolding in the README.

---

## 1. Five-second summary

An agent is asked to write a hidden pytest suite that codifies the
threat model for `mcp_vault` tool surfaces. The substrate seeds two
documents (`doc-alpha`, `doc-beta`) with explicit sentinel markers
in `mcp_vault/seed.py`. Several tool implementations in
`mcp_vault/tools.py` intentionally return or include those sentinel
values in responses (preview, export, audit), creating testable leak
surfaces. The agent's tests must catch leaks and also preserve
legitimate participant/admin behavior.

## 2. Why test-authoring is the right shape for this task

We ask for a test suite rather than a fix because the correct fix
shape is ambiguous in real systems. A useful test suite must capture
the dual contract: close the leak while preserving legitimate
participant and admin flows. The judge scores per-rubric coverage,
not a specific remediation.

## 3. The setup — what the agent sees

- The agent reviews a small Python MCP substrate mounted at `/repo`
  (`mcp_vault/`).
- Role tokens are encoded in `mcp_vault/common.py`: `admin-key`,
  `user-key` (alice), and `user2-key` (bob).
- The agent can call the tool functions exposed in `mcp_vault/app.py`.
- Seeded markers and canonical sentinel values live in
  `mcp_vault/seed.py` (e.g., `SENTINEL_ALPHA_DOC_BODY`,
  `SENTINEL_BETA_PRIVATE_NOTE`, `SENTINEL_DIAGNOSTIC_SECRET`).

## 4. The rubric / scenario-as-code

The canonical leak surfaces are implemented in `mcp_vault/tools.py`.
Two representative call paths (excerpt):

```py
def preview_document(store: Store, token: str, document_id: str) -> dict[str, str]:
    caller = verify_token(store, token)
    document = store.documents.get(document_id)
    if not document:
        raise KeyError("Not Found")
    if not document_allowed(store, caller, document):
        raise PermissionError("Forbidden")
    # Intentionally leaks private note in normal preview.
    return {"preview": f"{document.title}\n{document.body}\nNote: {document.private_note}"}
```

`seed.py` creates `doc-alpha` and `doc-beta` with explicit sentinel
strings; tests should assert for those sentinels where appropriate and
assert their absence where a denial is expected. Other vulnerable
surfaces include `export_document` (denial path leaking `document.title`),
`list_audit_records` (exposes secret_context), and `fetch_remote_attachment`
(internal-metadata return value). Use the above call sites as the
representative scenario-as-code when writing tests.

## 5. Why this is realistic

This mirrors common SaaS patterns: seeded private fields in persisted
rows, convenience endpoints that return full rows for developer ease,
and a fork/preview/export surface that can inadvertently re-expose
private fields. The duplicate/export/preview flows are realistic
laundering surfaces in multi-tenant apps.

## 6. How calibration runs work

This task is `pipeline: aspen` with `rubric_only: true`. The platform
auto-converts each `ground_truth_issues[]` entry into one judge
assertion, weighted by severity. The judge aggregates per-rubric
coverage into a reward ∈ [0,1] using the configured severity weights.

## 7. What the calibration should reveal (pending)

Calibration tables and pass@k are not yet available for this task in
the repo. When supplied, the README will include per-model tables (n,
mean, saturation, pass-rate) and per-rubric catch rates over the
aggregate sample.

## 8. How to read the calibration numbers

- The per-rubric `X/N` table shows how many samples caught each
  criterion out of the total runs. Higher spread across rubrics is a
  useful discrimination signal.
- `pass@k` is computed as `1 - C(n - c, k) / C(n, k)` (see README
  scaffolding). If calibration is pending, treat these sections as
  placeholders until fresh eval results are provided.

## 9. What this rubric does not measure

- Fix correctness or implementation style; only threat-model tests.
- Cross-language test-authoring ability (this task expects Python
  pytest).
- Test quality metrics such as naming or duplication; the rubric is
  coverage-focused.
