import pytest


@pytest.mark.asyncio
async def test_worker_registration(client):
    response = await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.25"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_worker_registration_duplicate(client):
    await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.25"},
    )
    response = await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.26"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_worker_heartbeat(client):
    reg = await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.25"},
    )
    worker_id = reg.json()["id"]

    response = await client.post(
        "/api/v1/workers/heartbeat",
        json={
            "id": worker_id,
            "cpu": 18,
            "ram": 24,
            "disk": 41,
            "temperature": 52,
            "busy": False,
            "network_speed": 100.0,
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_worker_heartbeat_unknown_worker(client):
    response = await client.post(
        "/api/v1/workers/heartbeat",
        json={
            "id": "nonexistent",
            "cpu": 18,
            "ram": 24,
            "disk": 41,
            "busy": False,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_workers(client):
    await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.25"},
    )
    await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-02", "hostname": "HP-02", "ip": "192.168.1.26"},
    )

    response = await client.get("/api/v1/workers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["worker_name"] == "HP-01"
    assert data[1]["worker_name"] == "HP-02"


@pytest.mark.asyncio
async def test_get_worker_by_id(client):
    reg = await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.25"},
    )
    worker_id = reg.json()["id"]

    response = await client.get(f"/api/v1/workers/{worker_id}")
    assert response.status_code == 200
    assert response.json()["worker_name"] == "HP-01"


@pytest.mark.asyncio
async def test_get_worker_not_found(client):
    response = await client.get("/api/v1/workers/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pause_resume_worker(client):
    reg = await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.25"},
    )
    worker_id = reg.json()["id"]

    pause_resp = await client.post(f"/api/v1/workers/{worker_id}/pause")
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "paused"

    resume_resp = await client.post(f"/api/v1/workers/{worker_id}/resume")
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "resumed"
