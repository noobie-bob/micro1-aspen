"""Weak cryptography tests for share-link token generation."""

from __future__ import annotations

import hashlib


def _project(client, auth_admin, team_id, name="crypto-test"):
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id, "name": name, "description": "test",
    })
    assert resp.status_code == 200
    return resp.get_json()


def test_share_link_token_is_cryptographically_random(client, auth_admin, auth_user, two_teams):
    """The share-link token must be cryptographically unpredictable.

    Three properties are verified together:
      1. Token is not a simple deterministic hash of the project ID
         (MD5, SHA-1, SHA-256 of the raw ID are all checked)
      2. Tokens for two different projects differ from each other
      3. Token is non-empty

    A fix that uses os.urandom or secrets.token_hex will pass all three;
    fixing only one weak derivation while keeping another will not.
    """
    proj1 = _project(client, auth_admin, two_teams["alpha"], name="proj-1")
    proj2 = _project(client, auth_admin, two_teams["alpha"], name="proj-2")

    resp1 = client.post(f"/projects/{proj1['id']}/share-link", headers=auth_user)
    resp2 = client.post(f"/projects/{proj2['id']}/share-link", headers=auth_user)
    assert resp1.status_code == 200
    assert resp2.status_code == 200

    token1 = resp1.get_json().get("share_token", "")
    token2 = resp2.get_json().get("share_token", "")

    assert token1, "share_token must be non-empty"
    assert token1 != token2, "share tokens for different projects must differ"

    # Verify token is not derived from the project ID via any common weak algorithm
    pid = proj1["id"]
    weak_derivations = [
        hashlib.md5(pid.encode()).hexdigest(),
        hashlib.sha1(pid.encode()).hexdigest(),
        hashlib.sha256(pid.encode()).hexdigest(),
    ]
    assert token1 not in weak_derivations, (
        f"share_token is a predictable hash of the project_id: {token1}"
    )
