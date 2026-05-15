"""Weak cryptography tests.

Covers rubric items:
  RUB-021  POST /projects/{id}/share-link must not use a predictable/reversible
           token (e.g. MD5 of project ID).
"""

from __future__ import annotations

import hashlib


def _create_project(client, auth_admin, team_id, name="crypto-test"):
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id, "name": name, "description": "test",
    })
    assert resp.status_code == 200
    return resp.get_json()


# ── RUB-021: Share tokens must be cryptographically random ─────────────────

def test_share_link_not_md5_of_project_id(client, auth_admin, auth_user, two_teams):
    """POST /projects/{id}/share-link must not derive the token from MD5
    of the project ID.

    RUB-021: share tokens must be cryptographically random, not predictable.
    """
    project = _create_project(client, auth_admin, two_teams["alpha"])
    project_id = project["id"]

    resp = client.post(f"/projects/{project_id}/share-link", headers=auth_user)
    assert resp.status_code == 200
    data = resp.get_json()
    share_token = data.get("share_token", "")

    # Compute what a naive MD5-based token would be
    md5_token = hashlib.md5(project_id.encode()).hexdigest()

    assert share_token != md5_token, (
        f"share_token is MD5 of project_id — predictable and reversible. "
        f"Token: {share_token}, MD5: {md5_token}"
    )


def test_share_link_tokens_are_unique(client, auth_admin, auth_user, two_teams):
    """Two calls to share-link for different projects should produce
    different tokens — weak derivation from a constant would fail this."""
    proj1 = _create_project(client, auth_admin, two_teams["alpha"], name="proj-1")
    proj2 = _create_project(client, auth_admin, two_teams["alpha"], name="proj-2")

    resp1 = client.post(f"/projects/{proj1['id']}/share-link", headers=auth_user)
    resp2 = client.post(f"/projects/{proj2['id']}/share-link", headers=auth_user)
    assert resp1.status_code == 200
    assert resp2.status_code == 200

    token1 = resp1.get_json().get("share_token", "")
    token2 = resp2.get_json().get("share_token", "")

    assert token1 != token2, "share tokens for different projects must differ"


def test_share_link_token_not_predictable_from_id(client, auth_admin, auth_user, two_teams):
    """The share token must not be a simple hash of the project ID using
    any common weak algorithm (MD5, SHA1 of just the ID)."""
    project = _create_project(client, auth_admin, two_teams["alpha"])
    project_id = project["id"]

    resp = client.post(f"/projects/{project_id}/share-link", headers=auth_user)
    assert resp.status_code == 200
    share_token = resp.get_json().get("share_token", "")

    # Check common weak derivations
    weak_tokens = [
        hashlib.md5(project_id.encode()).hexdigest(),
        hashlib.sha1(project_id.encode()).hexdigest(),
        hashlib.sha256(project_id.encode()).hexdigest(),
    ]
    assert share_token not in weak_tokens, (
        "share_token is a predictable hash of the project_id"
    )
