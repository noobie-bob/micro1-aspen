import django
import pytest

from projhub.app import state  # triggers settings.configure()

django.setup()

from django.test import Client  # noqa: E402 — must follow django.setup()


@pytest.fixture()
def client():
    state.reset()
    return Client()
