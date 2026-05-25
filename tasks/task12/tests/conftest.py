import multiprocessing
import time

import pytest
import requests

_PORT = 9301
_BASE = f"http://127.0.0.1:{_PORT}"


def _run_server():
    from projhub.app import app
    app.start(host="127.0.0.1", port=_PORT)


@pytest.fixture(scope="session", autouse=True)
def _server():
    p = multiprocessing.Process(target=_run_server)
    p.start()
    for _ in range(40):
        try:
            requests.get(f"{_BASE}/__test__/sent-reset-emails", timeout=0.3)
            break
        except Exception:
            time.sleep(0.25)
    yield
    p.terminate()
    p.join(timeout=5)


class _Client:
    def get(self, path, **kw):
        return requests.get(_BASE + path, **kw)

    def post(self, path, **kw):
        return requests.post(_BASE + path, **kw)


@pytest.fixture()
def client(_server):
    requests.post(f"{_BASE}/__test__/reset-state")
    return _Client()
