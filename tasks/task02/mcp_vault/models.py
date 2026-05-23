from dataclasses import dataclass, field
from typing import Any

@dataclass
class Caller:
    role: str
    user_id: str

@dataclass
class Organization:
    id: str
    name: str
    member_ids: list[str] = field(default_factory=list)

@dataclass
class Folder:
    id: str
    org_id: str
    name: str
    retention_label: str = ""

@dataclass
class Document:
    id: str
    folder_id: str
    title: str
    body: str
    owner: str = ""
    private_note: str = ""
    classification: str = "internal"

@dataclass
class AuditRecord:
    id: str
    document_id: str
    event: str
    secret_context: str = ""

@dataclass
class Store:
    orgs: dict[str, Organization] = field(default_factory=dict)
    folders: dict[str, Folder] = field(default_factory=dict)
    documents: dict[str, Document] = field(default_factory=dict)
    audit: dict[str, AuditRecord] = field(default_factory=dict)
    kv: dict[str, str] = field(default_factory=dict)
    next_ids: dict[str, int] = field(default_factory=lambda: {"org": 3, "folder": 3, "doc": 3, "audit": 3})

    def next_id(self, prefix: str) -> str:
        value = self.next_ids.get(prefix, 1)
        self.next_ids[prefix] = value + 1
        return f"{prefix}-{value}"

def asdict_public(obj: Any) -> dict[str, Any]:
    return dict(obj.__dict__)
