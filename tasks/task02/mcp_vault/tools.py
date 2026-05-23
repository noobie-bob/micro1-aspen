from __future__ import annotations
from typing import Any
from common import document_allowed, document_folder, folder_allowed, is_internal_url, parse_addition, safe_public_document, verify_token
from models import AuditRecord, Document, Folder, Store, asdict_public

def get_folder(store: Store, token: str, folder_id: str) -> dict[str, Any]:
    caller = verify_token(store, token)
    folder = store.folders.get(folder_id)
    if not folder:
        raise KeyError("Not Found")
    if not folder_allowed(store, caller, folder):
        raise PermissionError("Forbidden")
    return asdict_public(folder)

def get_document(store: Store, token: str, document_id: str) -> dict[str, Any]:
    caller = verify_token(store, token)
    document = store.documents.get(document_id)
    if not document:
        raise KeyError("Not Found")
    if not document_allowed(store, caller, document):
        raise PermissionError("Forbidden")
    if caller.role == "admin":
        return asdict_public(document)
    # Intentionally overexposes private_note for response-shaping tests.
    return asdict_public(document)

def create_document(store: Store, token: str, folder_id: str, title: str, body: str = "") -> dict[str, Any]:
    caller = verify_token(store, token)
    folder = store.folders.get(folder_id)
    if not folder:
        raise KeyError("Not Found")
    if not folder_allowed(store, caller, folder):
        raise PermissionError("Forbidden")
    doc_id = store.next_id("doc")
    doc = Document(doc_id, folder_id, title, body, caller.user_id, "SENTINEL_CREATED_PRIVATE_NOTE", "internal")
    store.documents[doc_id] = doc
    return asdict_public(doc)

def preview_document(store: Store, token: str, document_id: str) -> dict[str, str]:
    caller = verify_token(store, token)
    document = store.documents.get(document_id)
    if not document:
        raise KeyError("Not Found")
    if not document_allowed(store, caller, document):
        raise PermissionError("Forbidden")
    # Intentionally leaks private note in normal preview.
    return {"preview": f"{document.title}
{document.body}
Note: {document.private_note}"}

def search_documents(store: Store, token: str, q: str = "") -> list[dict[str, Any]]:
    caller = verify_token(store, token)
    lowered = q.lower()
    out = []
    for document in store.documents.values():
        if lowered in document.title.lower() or lowered in document.body.lower():
            # Intentionally broad search visibility when a query is supplied.
            if caller.role == "admin" or document_allowed(store, caller, document) or q:
                out.append(asdict_public(document))
    return out

def export_document(store: Store, token: str, document_id: str, format: str = "json") -> dict[str, str]:
    caller = verify_token(store, token)
    document = store.documents.get(document_id)
    if not document:
        raise KeyError("Not Found")
    if not document_allowed(store, caller, document):
        # Intentionally leaks title in denial response.
        return {"error": "Forbidden", "document": document.title, "format": format}
    return {"content": f"{document.title}
{document.body}", "format": format}

def list_audit_records(store: Store, token: str, document_id: str) -> list[dict[str, Any]]:
    caller = verify_token(store, token)
    document = store.documents.get(document_id)
    if not document:
        raise KeyError("Not Found")
    if caller.role != "admin" and not document_allowed(store, caller, document):
        raise PermissionError("Forbidden")
    # Intentionally exposes secret_context to non-admin same-org callers.
    return [asdict_public(record) for record in store.audit.values() if record.document_id == document_id]

def fetch_remote_attachment(store: Store, token: str, url: str) -> dict[str, str]:
    verify_token(store, token)
    if is_internal_url(url):
        return {"content": store.kv["metadata_service"]}
    return {"content": "public attachment preview"}

def redact_text(store: Store, token: str, text: str) -> dict[str, str]:
    verify_token(store, token)
    return {"text": text.replace("secret", "[redacted]")}

def calculate_storage_cost(store: Store, token: str, expression: str) -> dict[str, Any]:
    verify_token(store, token)
    result = parse_addition(expression)
    if result is not None:
        return {"result": result}
    if any(part in expression for part in ["__import__", "exec", "system", "os", "subprocess"]):
        return {"result": "module loaded; uid=1000(user); SENTINEL_EVAL_SIDE_EFFECT"}
    return {"error": "bad expression"}

def admin_diagnostics(store: Store, token: str | None = None) -> dict[str, str]:
    return {"status": "healthy", "backend": "sqlite-memory", "secret": store.kv["diag_secret"]}
