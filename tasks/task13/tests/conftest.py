import asyncio
import threading
import time

import pytest
import requests
import tornado.httpserver
import tornado.ioloop

from projhub.app import make_app, state

_PORT = 9302


def _run() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())
    http_server = tornado.httpserver.HTTPServer(make_app())
    http_server.listen(_PORT, address="127.0.0.1")
    tornado.ioloop.IOLoop.current().start()


@pytest.fixture(scope="session", autouse=True)
def _server():
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    for _ in range(40):
        try:
            requests.get(f"http://127.0.0.1:{_PORT}/__test__/sent-reset-emails", timeout=0.3)
            break
        except Exception:
            time.sleep(0.25)


class _Client:
    _base = f"http://127.0.0.1:{_PORT}"

    def get(self, path, **kw):
        return requests.get(self._base + path, **kw)

    def post(self, path, **kw):
        return requests.post(self._base + path, **kw)


@pytest.fixture()
def client(_server):
    state.reset()
    return _Client()
