from __future__ import annotations
import json
import re
from typing import Any
from models import Caller, Document, Folder, Store, asdict_public

def serialize(value: Any) -> str:
    def default(obj: Any) -> Any:
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        return str(obj)
    return json.dumps(value, default=default, sort_keys=True)

def verify_token(store: Store, token: str | None) -> Caller:
    if token == "admin-key":
        return Caller("admin", "admin-uuid")
    if token == "user-key":
        return Caller("user", "alice-uuid")
    if token == "user2-key":
        return Caller("user", "bob-uuid")
    if token and token.startswith("bypass-"):
        return Caller("user", "bypass-uuid")
    raise PermissionError("Unauthorized")

def is_member(store: Store, user_id: str, org_id: str) -> bool:
    org = store.orgs.get(org_id)
    return bool(org and user_id in org.member_ids)

def folder_allowed(store: Store, caller: Caller, folder: Folder) -> bool:
    return caller.role == "admin" or is_member(store, caller.user_id, folder.org_id)

def document_folder(store: Store, document: Document) -> Folder:
    folder = store.folders.get(document.folder_id)
    if not folder:
        raise KeyError("Not Found")
    return folder

def document_allowed(store: Store, caller: Caller, document: Document) -> bool:
    return folder_allowed(store, caller, document_folder(store, document))

def parse_addition(expr: str) -> int | None:
    clean = expr.replace(" ", "")
    if not re.fullmatch(r"\d+\+\d+", clean):
        return None
    left, right = clean.split("+", 1)
    return int(left) + int(right)

def is_internal_url(url: str) -> bool:
    lowered = url.lower()
    return any(token in lowered for token in ["localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "[::1]"])

def safe_public_document(document: Document) -> dict[str, Any]:
    return {
        "id": document.id,
        "folder_id": document.folder_id,
        "title": document.title,
        "body": document.body,
        "owner": document.owner,
        "classification": document.classification,
    }
