import pytest
from sanic_testing import TestManager

from projhub.app import app as _app, state

TestManager(_app)


@pytest.fixture()
def app():
    state.reset()
    return _app
