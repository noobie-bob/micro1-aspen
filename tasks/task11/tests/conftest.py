import pytest
from litestar.testing import TestClient

from projhub.app import app, state


@pytest.fixture()
def client():
    state.reset()
    with TestClient(app=app) as c:
        yield c
