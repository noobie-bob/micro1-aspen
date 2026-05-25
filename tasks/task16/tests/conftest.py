import pytest
from falcon import testing

from projhub.app import application, state


class _Resp:
    """Adapts falcon.testing.Result to match the requests.Response interface."""

    def __init__(self, result: testing.Result) -> None:
        self._r = result

    @property
    def status_code(self) -> int:
        return self._r.status_code

    def json(self) -> dict:
        return self._r.json


class _Client:
    def __init__(self, tc: testing.TestClient) -> None:
        self._tc = tc

    def get(self, path: str, **kw) -> _Resp:
        return _Resp(self._tc.simulate_get(path, **kw))

    def post(self, path: str, json=None, **kw) -> _Resp:
        return _Resp(self._tc.simulate_post(path, json=json, **kw))


@pytest.fixture()
def client() -> _Client:
    state.reset()
    return _Client(testing.TestClient(application))
