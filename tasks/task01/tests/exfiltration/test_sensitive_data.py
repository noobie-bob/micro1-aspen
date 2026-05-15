"""Sensitive data exposure and debug endpoint tests.

Covers rubric items:
  RUB-014  GET /debug/users must not return plaintext API tokens without admin auth
  RUB-015  GET /debug/config and GET /debug/env must not be accessible without admin auth
  RUB-027  GET /debug/dump must not be accessible without admin auth
"""

from __future__ import annotations


# ── RUB-014: /debug/users must not expose plaintext tokens ─────────────────

def test_debug_users_unauthenticated_forbidden(client):
    """GET /debug/users without authentication must return 401 or 403 or 404.

    RUB-014: the endpoint must require admin authentication or be removed.
    """
    resp = client.get("/debug/users")
    assert resp.status_code in (401, 403, 404), (
        f"unauthenticated GET /debug/users must not return 200, got {resp.status_code}"
    )


def test_debug_users_non_admin_forbidden(client, auth_user):
    """Non-admin GET /debug/users must return 403 or 404.

    RUB-014: non-admin users must not access user credentials.
    """
    resp = client.get("/debug/users", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"non-admin GET /debug/users must return 403/404, got {resp.status_code}"
    )


def test_debug_users_does_not_leak_tokens(client):
    """Even if accessible, /debug/users must not return plaintext API tokens.

    RUB-014: sensitive credential exposure check.
    """
    resp = client.get("/debug/users")
    body = resp.get_data(as_text=True)

    # Known API tokens from auth.py
    assert "admin-key" not in body, "plaintext admin token leaked via /debug/users"
    assert "user-key" not in body, "plaintext user token leaked via /debug/users"
    assert "user2-key" not in body, "plaintext user2 token leaked via /debug/users"


# ── RUB-015: /debug/config and /debug/env must not be accessible ───────────

def test_debug_config_unauthenticated_forbidden(client):
    """GET /debug/config without auth must return 401/403/404.

    RUB-015: prevents exposure of internal system configuration.
    """
    resp = client.get("/debug/config")
    assert resp.status_code in (401, 403, 404), (
        f"unauthenticated GET /debug/config must not return 200, got {resp.status_code}"
    )


def test_debug_config_non_admin_forbidden(client, auth_user):
    """Non-admin GET /debug/config must return 403 or 404."""
    resp = client.get("/debug/config", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"non-admin GET /debug/config must return 403/404, got {resp.status_code}"
    )


def test_debug_env_unauthenticated_forbidden(client):
    """GET /debug/env without auth must return 401/403/404.

    RUB-015: prevents exposure of environment variables.
    """
    resp = client.get("/debug/env")
    assert resp.status_code in (401, 403, 404), (
        f"unauthenticated GET /debug/env must not return 200, got {resp.status_code}"
    )


def test_debug_env_non_admin_forbidden(client, auth_user):
    """Non-admin GET /debug/env must return 403 or 404."""
    resp = client.get("/debug/env", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"non-admin GET /debug/env must return 403/404, got {resp.status_code}"
    )


# ── RUB-027: /debug/dump must not be accessible ───────────────────────────

def test_debug_dump_unauthenticated_forbidden(client):
    """GET /debug/dump without auth must return 401/403/404.

    RUB-027: prevents unauthenticated full database dump exposure.
    """
    resp = client.get("/debug/dump")
    assert resp.status_code in (401, 403, 404), (
        f"unauthenticated GET /debug/dump must not return 200, got {resp.status_code}"
    )


def test_debug_dump_non_admin_forbidden(client, auth_user):
    """Non-admin GET /debug/dump must return 403 or 404."""
    resp = client.get("/debug/dump", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"non-admin GET /debug/dump must return 403/404, got {resp.status_code}"
    )
