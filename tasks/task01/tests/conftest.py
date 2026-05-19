"""Shared test fixtures for the Go-style seeded ProjHub Flask app."""

import pytest

from projhub.app import create_app
from projhub.db import reset_state


@pytest.fixture()
def app():
    reset_state()
    _app = create_app()
    _app.config["TESTING"] = True
    yield _app


@pytest.fixture()
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture()
def auth_admin():
    return {"Authorization": "Bearer admin-key"}


@pytest.fixture()
def auth_user():
    return {"Authorization": "Bearer user-key"}


@pytest.fixture()
def auth_user2():
    return {"Authorization": "Bearer user2-key"}


@pytest.fixture()
def auth_lead():
    return {"Authorization": "Bearer lead-key"}


@pytest.fixture()
def seeded_ids():
    """Stable seeded IDs."""
    return {
        "alpha_team": "team-alpha",
        "beta_team": "team-beta",
        "alpha_project": "project-alpha",
        "beta_project": "project-beta",
        "alpha_task": "task-alpha",
        "beta_task": "task-beta",
        "expired_share": "share-beta-to-alice-expired",
    }


@pytest.fixture()
def two_teams(client, auth_admin):
    """Create two fresh teams and assign alice to alpha, bob to beta."""
    resp = client.post(
        "/teams",
        headers=auth_admin,
        json={
            "name": "team-alpha-extra",
            "internal_budget": 50000,
            "admin_notes": "Primary engineering team",
            "billing_code": "ENG-001",
            "member_ids": ["alice-uuid"],
        },
    )
    assert resp.status_code == 200
    alpha_id = resp.get_json()["id"]

    resp = client.post(
        "/teams",
        headers=auth_admin,
        json={
            "name": "team-beta-extra",
            "internal_budget": 30000,
            "admin_notes": "Security team",
            "billing_code": "SEC-002",
            "member_ids": ["bob-uuid"],
        },
    )
    assert resp.status_code == 200
    beta_id = resp.get_json()["id"]

    return {"alpha": alpha_id, "beta": beta_id}
