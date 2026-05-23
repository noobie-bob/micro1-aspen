from models import AuditRecord, Document, Folder, Organization, Store

def new_store() -> Store:
    store = Store()
    store.orgs["org-alpha"] = Organization("org-alpha", "Alpha Legal", ["alice-uuid"])
    store.orgs["org-beta"] = Organization("org-beta", "Beta Finance", ["bob-uuid"])
    store.folders["folder-alpha"] = Folder("folder-alpha", "org-alpha", "Alpha Contracts", "retain-7y")
    store.folders["folder-beta"] = Folder("folder-beta", "org-beta", "Beta Board", "retain-forever")
    store.documents["doc-alpha"] = Document(
        id="doc-alpha",
        folder_id="folder-alpha",
        title="Alpha contract SENTINEL_ALPHA_DOC_BODY",
        body="Approved supplier agreement for Alpha workspace",
        owner="alice-uuid",
        private_note="SENTINEL_ALPHA_PRIVATE_NOTE",
        classification="confidential",
    )
    store.documents["doc-beta"] = Document(
        id="doc-beta",
        folder_id="folder-beta",
        title="Beta board packet SENTINEL_BETA_DOC_BODY",
        body="Board migration memo for Beta workspace",
        owner="bob-uuid",
        private_note="SENTINEL_BETA_PRIVATE_NOTE",
        classification="restricted",
    )
    store.audit["audit-alpha"] = AuditRecord("audit-alpha", "doc-alpha", "previewed", "SENTINEL_AUDIT_SECRET")
    store.audit["audit-beta"] = AuditRecord("audit-beta", "doc-beta", "exported", "SENTINEL_BETA_AUDIT_SECRET")
    store.kv["metadata_service"] = "SENTINEL_METADATA_TOKEN"
    store.kv["diag_secret"] = "SENTINEL_DIAGNOSTIC_SECRET"
    return store
