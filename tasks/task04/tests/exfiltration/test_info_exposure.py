"""Information exposure via error responses.

Error responses must not leak internal implementation details to callers.
"""

from __future__ import annotations

import flask


def test_404_response_safe(client, auth_user):
    """A 404 response must not disclose the underlying framework version."""
    resp = client.get("/this/route/does/not/exist", headers=auth_user)
    assert resp.status_code == 404
    body = resp.get_data(as_text=True)
    assert "framework_version" not in body, "404 response leaks framework_version key"
    assert flask.__version__ not in body, "404 response contains Flask version string"


def test_500_error_response_safe(client, auth_admin, two_teams):
    """A 500 response must not disclose stack traces, file paths, or runtime version.

    All three leakage classes are verified together — a fix must suppress
    every class of verbose error output, not just one.
    """
    resp = client.get("/debug/error", headers=auth_admin)
    assert resp.status_code == 500
    body = resp.get_data(as_text=True)

    assert "Traceback (most recent call last)" not in body, (
        "500 response exposes full Python traceback"
    )
    assert 'File "/' not in body, (
        "500 response exposes internal file paths"
    )
    assert "python_version" not in body, (
        "500 response exposes Python runtime version"
    )

    data = resp.get_json() or {}
    assert "traceback" not in data, (
        "500 response JSON serialises raw traceback into 'traceback' field"
    )


def test_generic_error_handler_safe(client, auth_user):
    """Application-wide error handler must not expose internals for any endpoint."""
    resp = client.get(
        "/search/tasks?q=' OR 1=1; INVALID SQL THAT ERRORS --",
        headers=auth_user,
    )
    body = resp.get_data(as_text=True)
    assert "Traceback (most recent call last)" not in body, (
        "Generic error response contains Python traceback"
    )
    assert 'File "/' not in body, (
        "Generic error response contains internal file paths"
    )
