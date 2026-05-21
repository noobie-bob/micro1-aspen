import pytest
from fastapi.testclient import TestClient

from taskhub.db import reset_state
from taskhub.main import create_app


@pytest.fixture()
def app():
    reset_state()
    return create_app()


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
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
