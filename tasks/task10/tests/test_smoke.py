from __future__ import annotations


async def test_alice_login_succeeds(app):
    _, response = await app.asgi_client.post(
        "/auth/login", json={"email": "alice@example.com", "password": "old-password"}
    )
    assert response.status == 200
    assert "access_token" in response.json


async def test_forgot_password_accepted(app):
    _, response = await app.asgi_client.post(
        "/auth/password/forgot", json={"email": "alice@example.com"}
    )
    assert response.status == 202


async def test_reset_with_outbox_token_succeeds(app):
    await app.asgi_client.post("/auth/password/forgot", json={"email": "alice@example.com"})
    _, outbox = await app.asgi_client.get("/__test__/sent-reset-emails")
    token = outbox.json["emails"][-1]["token"]
    _, response = await app.asgi_client.post(
        "/auth/password/reset", json={"token": token, "new_password": "new-pass"}
    )
    assert response.status == 200
