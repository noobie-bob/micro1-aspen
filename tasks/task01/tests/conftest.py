"""Shared test fixtures for ProjHub.

Provides Flask test client, auth headers for three roles (admin, user alice,
user bob), and a helper to set up the standard two-team topology used in
all smoke and exfiltration tests.
"""

import pytest

from projhub.app import create_app
from projhub.db import TEAM_MEMBERS, reset_state


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
def two_teams(client, auth_admin):
    """Create two teams and assign alice to team-alpha, bob to team-beta.

    Returns a dict with team IDs:
        {"alpha": "<team-alpha-id>", "beta": "<team-beta-id>"}
    """
    # Create team-alpha
    resp = client.post("/teams", headers=auth_admin, json={
        "name": "team-alpha",
        "internal_budget": 50000,
        "admin_notes": "Primary engineering team",
        "billing_code": "ENG-001",
        "member_ids": ["alice-uuid"],
    })
    assert resp.status_code == 200
    alpha_id = resp.get_json()["id"]

    # Create team-beta
    resp = client.post("/teams", headers=auth_admin, json={
        "name": "team-beta",
        "internal_budget": 30000,
        "admin_notes": "Security team",
        "billing_code": "SEC-002",
        "member_ids": ["bob-uuid"],
    })
    assert resp.status_code == 200
    beta_id = resp.get_json()["id"]

    return {"alpha": alpha_id, "beta": beta_id}
