import pytest

from app import call_tool, reset_store


@pytest.fixture()
def app():
    reset_store()
    return call_tool


@pytest.fixture()
def tool(app):
    return app


@pytest.fixture()
def auth_admin():
    return "admin-key"


@pytest.fixture()
def auth_user():
    return "user-key"


@pytest.fixture()
def auth_user2():
    return "user2-key"
