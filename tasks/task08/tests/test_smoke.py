from __future__ import annotations


def test_alice_login_succeeds(client):
    resp = client.post("/auth/login", json={"email": "alice@example.com", "password": "old-password"})
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_forgot_password_accepted(client):
    resp = client.post("/auth/password/forgot", json={"email": "alice@example.com"})
    assert resp.status_code == 202


def test_reset_with_outbox_token_succeeds(client):
    client.post("/auth/password/forgot", json={"email": "alice@example.com"})
    token = client.get("/__test__/sent-reset-emails").get_json()["emails"][-1]["token"]
    resp = client.post("/auth/password/reset", json={"token": token, "new_password": "new-pass"})
    assert resp.status_code == 200

