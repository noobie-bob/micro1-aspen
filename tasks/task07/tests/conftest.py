import pytest

@pytest.fixture()
def full_ticket_payload():
    return {"x": 1, "y": 2}

@pytest.fixture()
def compact_ticket_payload():
    return {"x": 1}
