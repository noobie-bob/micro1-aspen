"""Information exposure via error responses tests.

The application's global error handler and 404 handler must not leak
internal implementation details to callers.  Three specific classes of
leakage are tested:

  1. Full Python stack traces (``Traceback (most recent call last)``)
  2. Internal file paths (e.g. ``/repo/projhub/...``, ``/usr/local/lib/...``)
  3. Framework version information (e.g. Flask version string)

Covers rubric item:
  RUB-020  Error responses must not include full Python stack traces,
           internal file paths, or framework version information.
"""

from __future__ import annotations

import flask


def _create_project(client, auth_admin, team_id):
    resp = client.post("/projects", headers=auth_admin, json={
        "team_id": team_id, "name": "info-test", "description": "test",
    })
    assert resp.status_code == 200
    return resp.get_json()


def _create_task(client, headers, project_id):
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json={
        "title": "info-task", "description": "test", "priority": "medium",
    })
    assert resp.status_code == 200
    return resp.get_json()


# ── RUB-020: 404 responses must not leak framework version ─────────────────

def test_404_response_does_not_contain_framework_version(client, auth_user):
    """A 404 error response must not include the Flask framework version.

    The application's 404 handler must return a generic error body without
    disclosing what framework or version is running.
    """
    resp = client.get("/this/route/does/not/exist", headers=auth_user)
    assert resp.status_code == 404

    body = resp.get_data(as_text=True)

    # The response must not contain a 'framework_version' key
    assert "framework_version" not in body, (
        "404 response contains 'framework_version' — leaks framework info"
    )

    # The response must not contain the actual Flask version string
    assert flask.__version__ not in body, (
        f"404 response contains Flask version '{flask.__version__}'"
    )


# ── RUB-020: 500 responses must not leak full Python stack traces ──────────

def test_500_response_does_not_contain_stack_trace(client, auth_admin, two_teams):
    """A 500 error response must not include a full Python stack trace.

    When the application raises an unhandled exception, the error response
    sent to the caller must NOT contain 'Traceback (most recent call last)'
    or similar Python traceback output.  Returning raw tracebacks reveals
    internal code structure, file paths, and library internals.
    """
    # Trigger a 500 via the debug error endpoint which deliberately raises
    resp = client.get("/debug/error", headers=auth_admin)
    assert resp.status_code == 500

    body = resp.get_data(as_text=True)

    # Must not contain the Python traceback header
    assert "Traceback (most recent call last)" not in body, (
        "500 response contains full Python traceback — "
        "error handler must not expose stack traces to callers"
    )


def test_500_response_does_not_contain_internal_file_paths(client, auth_admin, two_teams):
    """A 500 error response must not expose internal file paths.

    Paths like '/repo/projhub/...', '/usr/local/lib/python...', or
    'File \"/...' disclose the server's directory layout and installed
    packages to an attacker.
    """
    resp = client.get("/debug/error", headers=auth_admin)
    assert resp.status_code == 500

    body = resp.get_data(as_text=True)

    # Must not contain Python file-path references from tracebacks
    assert 'File "/' not in body, (
        "500 response contains internal file paths (Unix-style) — "
        "error handler leaks server directory layout"
    )

    # Must not contain the 'traceback' key that wraps raw stack output
    data = resp.get_json()
    assert "traceback" not in data, (
        "500 response JSON contains a 'traceback' field — "
        "raw stack trace must not be serialised into error responses"
    )


def test_500_response_does_not_contain_python_version(client, auth_admin, two_teams):
    """A 500 error response must not disclose the Python runtime version."""
    resp = client.get("/debug/error", headers=auth_admin)
    assert resp.status_code == 500

    body = resp.get_data(as_text=True)

    assert "python_version" not in body, (
        "500 response contains 'python_version' field"
    )


# ── RUB-020: Verify via the global error handler (not just /debug) ─────────

def test_global_error_handler_does_not_leak_traceback(client, auth_admin, auth_user, two_teams):
    """Force a server error through a normal endpoint and verify the global
    error handler does not expose stack traces or file paths.

    This tests the application-wide @app.errorhandler(Exception) response,
    not just a specific debug endpoint.
    """
    # Attempt to trigger a 500 through the search endpoint with crafted input
    # that may cause an internal error
    resp = client.get(
        "/search/tasks?q=' OR 1=1; INVALID SQL THAT ERRORS --",
        headers=auth_user,
    )
    body = resp.get_data(as_text=True)

    # Whether the endpoint returns 400 or 500, it must not contain tracebacks
    assert "Traceback (most recent call last)" not in body, (
        "Error response from search endpoint contains full Python traceback"
    )
    assert 'File "/' not in body, (
        "Error response from search endpoint contains internal file paths"
    )
