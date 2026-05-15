"""Admin endpoint access control tests.

Covers rubric items:
  RUB-010  Non-admin GET /admin/audit-log returns 403
  RUB-011  Non-admin GET /admin/reports/summary returns 403
"""

from __future__ import annotations


# ── RUB-010: Non-admin cannot access audit log ─────────────────────────────

def test_non_admin_audit_log_forbidden(client, auth_user, two_teams):
    """Non-admin GET /admin/audit-log must return 403.

    RUB-010: prevents non-admin access to the system audit log.
    """
    resp = client.get("/admin/audit-log", headers=auth_user)
    assert resp.status_code == 403, (
        f"non-admin GET /admin/audit-log must return 403, got {resp.status_code}"
    )


def test_non_admin_audit_log_forbidden_user2(client, auth_user2, two_teams):
    """Bob also must not access the audit log."""
    resp = client.get("/admin/audit-log", headers=auth_user2)
    assert resp.status_code == 403


# ── RUB-011: Non-admin cannot access org summary report ────────────────────

def test_non_admin_summary_report_forbidden(client, auth_user, two_teams):
    """Non-admin GET /admin/reports/summary must return 403.

    RUB-011: prevents non-admin access to org-wide metrics and budget data.
    """
    resp = client.get("/admin/reports/summary", headers=auth_user)
    assert resp.status_code == 403, (
        f"non-admin GET /admin/reports/summary must return 403, got {resp.status_code}"
    )


def test_non_admin_summary_report_forbidden_user2(client, auth_user2, two_teams):
    """Bob also must not access the summary report."""
    resp = client.get("/admin/reports/summary", headers=auth_user2)
    assert resp.status_code == 403
