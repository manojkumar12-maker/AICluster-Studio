import pytest


@pytest.mark.asyncio
async def test_rate_limiter_configured():
    """Verify the rate limiter is configured on the app."""
    from app.main import app
    assert hasattr(app.state, "limiter"), "Rate limiter not configured on app"


@pytest.mark.asyncio
async def test_health_not_rate_limited(client):
    """Verify public health endpoint is accessible (no aggressive limit)."""
    for _ in range(5):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
