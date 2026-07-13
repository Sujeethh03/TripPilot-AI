"""Integration tests for auth endpoints (against the test database)."""

from httpx import AsyncClient

_CREDS = {"email": "traveller@trippilot.ai", "password": "supersecret1", "name": "Traveller"}


async def test_register_login_me_flow(client: AsyncClient) -> None:
    # Register
    r = await client.post("/api/v1/auth/register", json=_CREDS)
    assert r.status_code == 201
    assert r.json()["email"] == _CREDS["email"]
    assert "password" not in r.json()

    # Login
    r = await client.post(
        "/api/v1/auth/login", json={"email": _CREDS["email"], "password": _CREDS["password"]}
    )
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Authenticated /me
    r = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == _CREDS["email"]


async def test_duplicate_email_conflicts(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_CREDS)
    r = await client.post("/api/v1/auth/register", json=_CREDS)
    assert r.status_code == 409


async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=_CREDS)
    r = await client.post(
        "/api/v1/auth/login", json={"email": _CREDS["email"], "password": "wrongpass1"}
    )
    assert r.status_code == 401


async def test_me_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/me")).status_code == 401


async def test_me_rejects_bad_token(client: AsyncClient) -> None:
    r = await client.get("/api/v1/me", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401
