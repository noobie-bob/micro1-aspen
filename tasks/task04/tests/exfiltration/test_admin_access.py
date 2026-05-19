"""Admin endpoint access control tests.

Non-admin users must be denied access to admin-only management endpoints.
"""

from __future__ import annotations


def test_non_admin_cannot_access_admin_endpoints(client, auth_user, two_teams):
    """Both /admin/audit-log and /admin/reports/summary must return 403 for
    non-admin callers — neither endpoint must leak org-wide data to participants."""
    audit_resp = client.get("/admin/audit-log", headers=auth_user)
    assert audit_resp.status_code == 403, (
        f"non-admin GET /admin/audit-log must return 403, got {audit_resp.status_code}"
    )

    report_resp = client.get("/admin/reports/summary", headers=auth_user)
    assert report_resp.status_code == 403, (
        f"non-admin GET /admin/reports/summary must return 403, got {report_resp.status_code}"
    )
