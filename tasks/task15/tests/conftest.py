import pytest
import requests
import cherrypy

from projhub.app import Root, state

_PORT = 9304


@pytest.fixture(scope="session", autouse=True)
def _server():
    cherrypy.config.update({
        "server.socket_host": "127.0.0.1",
        "server.socket_port": _PORT,
        "environment": "test_suite",
        "log.screen": False,
    })
    cherrypy.tree.mount(Root(), "/")
    cherrypy.engine.start()
    cherrypy.engine.wait(cherrypy.engine.states.STARTED)
    yield
    cherrypy.engine.stop()
    cherrypy.engine.wait(cherrypy.engine.states.STOPPED)


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
