import os
import subprocess
import sys
import time

import pytest
import requests

_PORT = 9301
_BASE = f"http://127.0.0.1:{_PORT}"


@pytest.fixture(scope="session", autouse=True)
def _server():
    env = {**os.environ, "PROJHUB_PORT": str(_PORT)}
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proc = subprocess.Popen(
        [sys.executable, os.path.join(root, "projhub", "app.py")],
        env=env,
        cwd=root,
    )
    for _ in range(40):
        try:
            requests.get(f"{_BASE}/__test__/sent-reset-emails", timeout=0.5)
            break
        except Exception:
            time.sleep(0.25)
    yield
    proc.terminate()
    proc.wait(timeout=5)


class _Client:
    def get(self, path, **kw):
        return requests.get(_BASE + path, **kw)

    def post(self, path, **kw):
        return requests.post(_BASE + path, **kw)


@pytest.fixture()
def client(_server):
    requests.post(f"{_BASE}/__test__/reset-state")
    return _Client()
