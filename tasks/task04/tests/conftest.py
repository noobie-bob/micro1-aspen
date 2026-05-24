import pytest

from projhub.app import create_app
from projhub.db import reset_state


@pytest.fixture()
def app():
    reset_state()
    app = create_app()
    app.config["TESTING"] = True
    return app


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
    return {
        "alpha_project": "project-alpha",
        "beta_project": "project-beta",
        "alpha_task": "task-alpha",
        "beta_task": "task-beta",
        "alpha_team": "team-alpha",
        "beta_team": "team-beta",
    }
