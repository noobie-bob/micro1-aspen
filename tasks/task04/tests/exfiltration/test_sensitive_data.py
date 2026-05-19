"""Sensitive data exposure via debug and diagnostic endpoints.

Debug endpoints that expose credentials, configuration, or raw database state
must not be accessible without administrative authentication.
"""

from __future__ import annotations

from projhub.auth import VALID_TOKENS


def test_debug_users_endpoint_locked_down(client, auth_user):
    """The user-listing debug endpoint must not expose plaintext API credentials.

    Checked at three levels: unauthenticated access, non-admin access, and
    actual token presence in the response body — all must be blocked.
    """
    # Unauthenticated
    resp_unauth = client.get("/debug/users")
    assert resp_unauth.status_code in (401, 403, 404), (
        f"unauthenticated /debug/users must not return 200, got {resp_unauth.status_code}"
    )

    # Non-admin authenticated
    resp_user = client.get("/debug/users", headers=auth_user)
    assert resp_user.status_code in (403, 404), (
        f"non-admin /debug/users must return 403/404, got {resp_user.status_code}"
    )

    # Token values must not appear even if endpoint responds
    body = resp_unauth.get_data(as_text=True)
    for token in VALID_TOKENS:
        assert token not in body, f"plaintext token '{token}' leaked via /debug/users"


def test_debug_config_env_endpoints_locked_down(client, auth_user):
    """System configuration and environment variable endpoints must be inaccessible
    to unauthenticated and non-admin callers."""
    for endpoint in ("/debug/config", "/debug/env"):
        unauth = client.get(endpoint)
        assert unauth.status_code in (401, 403, 404), (
            f"unauthenticated {endpoint} must not return 200, got {unauth.status_code}"
        )
        non_admin = client.get(endpoint, headers=auth_user)
        assert non_admin.status_code in (403, 404), (
            f"non-admin {endpoint} must return 403/404, got {non_admin.status_code}"
        )


def test_debug_dump_locked_down(client, auth_user):
    """The database dump endpoint must not be accessible to unauthenticated
    or non-admin callers."""
    unauth = client.get("/debug/dump")
    assert unauth.status_code in (401, 403, 404), (
        f"unauthenticated /debug/dump must not return 200, got {unauth.status_code}"
    )
    non_admin = client.get("/debug/dump", headers=auth_user)
    assert non_admin.status_code in (403, 404), (
        f"non-admin /debug/dump must return 403/404, got {non_admin.status_code}"
    )
