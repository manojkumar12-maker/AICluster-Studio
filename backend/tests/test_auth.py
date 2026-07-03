import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_unknown_user(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "test123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_missing_fields(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_empty_body(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_json(client):
    response = await client.post(
        "/api/v1/auth/login",
        content=b"not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
