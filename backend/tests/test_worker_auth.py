import pytest


@pytest.mark.asyncio
async def test_worker_registration_with_jwt(client):
    """Verify worker registration works with JWT token (admin user)."""
    response = await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.25"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_worker_registration_without_auth_fails():
    """Verify worker registration fails without auth."""
    from app.main import app
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/workers/register",
            json={"name": "HP-03", "hostname": "HP-03", "ip": "192.168.1.27"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_worker_heartbeat_with_jwt(client):
    """Verify worker heartbeat works with JWT."""
    reg = await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.25"},
    )
    worker_id = reg.json()["id"]
    response = await client.post(
        "/api/v1/workers/heartbeat",
        json={"id": worker_id, "cpu": 18, "ram": 24, "disk": 41, "busy": False, "network_speed": 100.0},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
