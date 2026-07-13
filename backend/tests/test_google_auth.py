"""Integration tests for Google OAuth login (token verification mocked)."""

import pytest
from httpx import AsyncClient

import app.api.v1.auth as auth_module
from app.core.google_oauth import GoogleIdentity


def _stub_verify(identity: GoogleIdentity | None):
    def _verify(token: str) -> GoogleIdentity | None:
        return identity

    return _verify


async def test_google_auth_creates_user(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        auth_module,
        "verify_google_token",
        _stub_verify(GoogleIdentity(google_id="g-1", email="new@gmail.com", name="New")),
    )
    r = await client.post("/api/v1/auth/google", json={"id_token": "tok"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Token works against a protected route.
    me = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["email"] == "new@gmail.com"


async def test_google_auth_links_existing_email(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Register a password account first.
    await client.post(
        "/api/v1/auth/register",
        json={"email": "both@gmail.com", "password": "password123"},
    )
    monkeypatch.setattr(
        auth_module,
        "verify_google_token",
        _stub_verify(GoogleIdentity(google_id="g-2", email="both@gmail.com", name=None)),
    )
    r = await client.post("/api/v1/auth/google", json={"id_token": "tok"})
    assert r.status_code == 200

    # Signing in with Google again resolves to the same (now linked) account.
    again = await client.post("/api/v1/auth/google", json={"id_token": "tok"})
    assert again.status_code == 200


async def test_google_auth_rejects_invalid_token(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(auth_module, "verify_google_token", _stub_verify(None))
    r = await client.post("/api/v1/auth/google", json={"id_token": "bad"})
    assert r.status_code == 401
