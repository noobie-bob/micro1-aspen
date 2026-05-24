from __future__ import annotations


def test_same_org_participant_reads_alpha_document(tool, auth_user):
    doc = tool("get_document", {"token": auth_user, "document_id": "doc-alpha"})
    assert doc["id"] == "doc-alpha"


def test_same_org_participant_searches_alpha_document(tool, auth_user):
    results = tool(
        "search_documents", {"token": auth_user, "q": "SENTINEL_ALPHA_DOC_BODY"}
    )
    assert any(doc["id"] == "doc-alpha" for doc in results)


def test_admin_reads_beta_document(tool, auth_admin):
    doc = tool("get_document", {"token": auth_admin, "document_id": "doc-beta"})
    assert doc["id"] == "doc-beta"


def test_second_participant_reads_beta_document(tool, auth_user2):
    doc = tool("get_document", {"token": auth_user2, "document_id": "doc-beta"})
    assert doc["id"] == "doc-beta"
