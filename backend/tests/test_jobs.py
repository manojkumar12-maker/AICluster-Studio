import pytest


@pytest.mark.asyncio
async def test_create_job(client):
    response = await client.post(
        "/api/v1/jobs",
        json={"type": "test", "payload": {"command": "echo hello"}, "priority": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "test"
    assert data["status"] == "queued"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_jobs(client):
    await client.post(
        "/api/v1/jobs",
        json={"type": "job-1", "payload": {}, "priority": 1},
    )
    await client.post(
        "/api/v1/jobs",
        json={"type": "job-2", "payload": {}, "priority": 3},
    )

    response = await client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_job_by_id(client):
    create_resp = await client.post(
        "/api/v1/jobs",
        json={"type": "test-job", "payload": {"key": "value"}, "priority": 2},
    )
    job_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["type"] == "test-job"


@pytest.mark.asyncio
async def test_get_job_not_found(client):
    response = await client.get("/api/v1/jobs/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_job(client):
    create_resp = await client.post(
        "/api/v1/jobs",
        json={"type": "cancel-test", "payload": {}, "priority": 2},
    )
    job_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_job_not_found(client):
    response = await client.delete("/api/v1/jobs/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_already_finished_job(client):
    create_resp = await client.post(
        "/api/v1/jobs",
        json={"type": "test", "payload": {}, "priority": 2},
    )
    job_id = create_resp.json()["id"]

    await client.delete(f"/api/v1/jobs/{job_id}")
    response = await client.delete(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_job_default_priority(client):
    response = await client.post(
        "/api/v1/jobs",
        json={"type": "default-priority", "payload": {}},
    )
    assert response.status_code == 200
    assert response.json()["priority"] == 2
