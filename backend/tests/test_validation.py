import pytest


@pytest.mark.asyncio
async def test_register_worker_missing_fields(client):
    response = await client.post(
        "/api/v1/workers/register",
        json={"name": "test"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_worker_empty_name(client):
    response = await client.post(
        "/api/v1/workers/register",
        json={"name": "", "hostname": "", "ip": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_worker_invalid_json(client):
    response = await client.post(
        "/api/v1/workers/register",
        content=b"not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_duplicate_name(client):
    resp1 = await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.50"},
    )
    assert resp1.status_code == 200
    id1 = resp1.json()["id"]

    resp2 = await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.51"},
    )
    assert resp2.status_code == 200
    id2 = resp2.json()["id"]

    assert id1 == id2


@pytest.mark.asyncio
async def test_heartbeat_malformed(client):
    reg = await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.50"},
    )
    worker_id = reg.json()["id"]

    response = await client.post(
        "/api/v1/workers/heartbeat",
        json={"id": worker_id, "cpu": "not-a-number"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_heartbeat_out_of_range(client):
    reg = await client.post(
        "/api/v1/workers/register",
        json={"name": "HP-01", "hostname": "HP-01", "ip": "192.168.1.50"},
    )
    worker_id = reg.json()["id"]

    response = await client.post(
        "/api/v1/workers/heartbeat",
        json={
            "id": worker_id, "cpu": 150, "ram": 50, "disk": 50,
            "busy": False,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_heartbeat_unknown_worker(client):
    response = await client.post(
        "/api/v1/workers/heartbeat",
        json={
            "id": "nonexistent-id",
            "cpu": 10, "ram": 20, "disk": 30,
            "busy": False,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_heartbeat_missing_id(client):
    response = await client.post(
        "/api/v1/workers/heartbeat",
        json={"cpu": 10, "ram": 20, "disk": 30},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_worker_not_found(client):
    response = await client.get("/api/v1/workers/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_job_not_found(client):
    response = await client.get("/api/v1/jobs/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_job_not_found(client):
    response = await client.delete("/api/v1/jobs/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_job_invalid_priority(client):
    response = await client.post(
        "/api/v1/jobs",
        json={"type": "test", "payload": {}, "priority": 0},
    )
    assert response.status_code == 422

    response = await client.post(
        "/api/v1/jobs",
        json={"type": "test", "payload": {}, "priority": 6},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_job_invalid_json(client):
    response = await client.post(
        "/api/v1/jobs",
        content=b"not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_dashboard_health_endpoints(client):
    health = await client.get("/api/v1/health")
    assert health.status_code == 200
    hdata = health.json()
    assert hdata["status"] == "ok"
    assert hdata["database"] == "connected"

    dash = await client.get("/api/v1/dashboard")
    assert dash.status_code == 200
    ddata = dash.json()
    assert ddata["total_workers"] == 0


@pytest.mark.asyncio
async def test_root_and_docs(client):
    root = await client.get("/")
    assert root.status_code == 200
    rdata = root.json()
    assert "app" in rdata
    assert "version" in rdata

    docs = await client.get("/docs")
    assert docs.status_code == 200

    redoc = await client.get("/redoc")
    assert redoc.status_code == 200


@pytest.mark.asyncio
async def test_logs_filtering(client):
    logs = await client.get("/api/v1/logs")
    assert logs.status_code == 200
    assert isinstance(logs.json(), list)

    logs_filtered = await client.get("/api/v1/logs?level=INFO")
    assert logs_filtered.status_code == 200
