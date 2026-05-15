"""Information exposure via error responses tests.

Covers rubric items:
  RUB-020  Error responses must not include full Python stack traces,
           internal file paths, or framework version information.
"""

from __future__ import annotations


# ── RUB-020: Error responses must not leak internal details ────────────────

def test_404_does_not_leak_framework_version(client, auth_user):
    """404 responses must not include framework version information.

    RUB-020: framework_version, flask version strings, etc. must not
    appear in error responses.
    """
    resp = client.get("/nonexistent/endpoint/that/does/not/exist",
                      headers=auth_user)
    # Expect 404
    body = resp.get_data(as_text=True)

    assert "framework_version" not in body, (
        "404 response leaks framework_version"
    )
    # Check for common Flask version patterns
    import flask
    assert flask.__version__ not in body, (
        f"404 response leaks Flask version {flask.__version__}"
    )


def test_500_does_not_leak_stack_trace(client, auth_admin):
    """500 responses must not include full Python stack traces.

    RUB-020: traceback, internal file paths must not appear.
    """
    # Trigger a deliberate error via the debug endpoint
    resp = client.get("/debug/error", headers=auth_admin)

    if resp.status_code == 500:
        body = resp.get_data(as_text=True)
        assert "traceback" not in body.lower() or "Traceback (most recent" not in body, (
            "500 response leaks full Python stack trace"
        )
        assert "File \"/" not in body and 'File "C:' not in body, (
            "500 response leaks internal file paths"
        )


def test_error_does_not_leak_python_version(client, auth_admin):
    """Error responses must not leak Python version."""
    resp = client.get("/debug/error", headers=auth_admin)
    if resp.status_code == 500:
        body = resp.get_data(as_text=True)
        assert "python_version" not in body, (
            "error response leaks python_version"
        )


def test_general_500_no_traceback(client, auth_admin):
    """Any 500 response from the app error handler must not include traceback."""
    # Access a path that would trigger the global error handler
    resp = client.get("/tasks/INVALID_ID_THAT_MIGHT_ERROR", headers=auth_admin)
    body = resp.get_data(as_text=True)

    # If it's a 500, check for traceback leakage
    if resp.status_code == 500:
        assert "Traceback (most recent" not in body, (
            "global error handler leaks Python traceback"
        )
