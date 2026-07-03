import pytest


@pytest.mark.asyncio
async def test_dashboard_empty(client):
    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_workers"] == 0
    assert data["online"] == 0
    assert data["offline"] == 0
    assert data["idle"] == 0
    assert data["busy"] == 0
    assert data["running_jobs"] == 0


@pytest.mark.asyncio
async def test_dashboard_with_workers(client):
    await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.25"},
    )
    await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-02", "hostname": "HP-02", "ip": "192.168.1.26"},
    )

    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_workers"] == 2
    assert data["online"] == 2
    assert data["offline"] == 0


@pytest.mark.asyncio
async def test_dashboard_with_busy_worker(client):
    reg = await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.25"},
    )
    worker_id = reg.json()["id"]

    await client.post(
        "/api/v1/workers/heartbeat",
        json={
            "id": worker_id, "cpu": 80, "ram": 60, "disk": 50,
            "busy": True, "network_speed": 100.0,
        },
    )

    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_workers"] == 1
    assert data["busy"] == 1
    assert data["idle"] == 0
