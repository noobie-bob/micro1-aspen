import pytest

from projhub.app import app, state


@pytest.fixture()
def client():
    state.reset()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
