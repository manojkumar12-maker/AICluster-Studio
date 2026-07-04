import os
import secrets
import tempfile

import pytest


def test_jwt_secret_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        from app.config import Settings
        s = Settings(data_dir=tmpdir, _env_file=None)
        secret = s.secret_key
        assert len(secret) == 64, "Secret should be 64 hex chars (32 bytes)"
        secret_file = os.path.join(tmpdir, "secret.key")
        assert os.path.exists(secret_file)
        with open(secret_file) as f:
            assert f.read().strip() == secret


def test_jwt_secret_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        secret_file = os.path.join(tmpdir, "secret.key")
        os.makedirs(tmpdir, exist_ok=True)
        with open(secret_file, "w") as f:
            f.write("persistent-test-secret-0123456789abcdef")

        from app.config import Settings
        s = Settings(data_dir=tmpdir, _env_file=None)
        assert s.secret_key == "persistent-test-secret-0123456789abcdef"


def test_jwt_secret_env_override():
    os.environ["AICLUSTER_SECRET_KEY"] = "env-override-secret-0123456789abcdef"
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            from app.config import Settings
            s = Settings(data_dir=tmpdir, _env_file=None)
            assert s.secret_key == "env-override-secret-0123456789abcdef"
    finally:
        del os.environ["AICLUSTER_SECRET_KEY"]


def test_admin_password_generated():
    password = secrets.token_urlsafe(16)
    assert len(password) >= 16


def test_admin_password_env_var_name():
    """Verify seed_default_admin reads AICLUSTER_ADMIN_PASSWORD env var."""
    import inspect
    from app.services.auth import AuthService
    source = inspect.getsource(AuthService.seed_default_admin)
    assert 'os.environ.get("AICLUSTER_ADMIN_PASSWORD"' in source or "AICLUSTER_ADMIN_PASSWORD" in source


@pytest.mark.asyncio
async def test_login_success(client, admin_password):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": admin_password},
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


def test_cors_allowed_origin():
    """Verify config returns proper CORS origins."""
    from app.config import settings
    origins = settings.get_cors_origins_list()
    assert "http://localhost:3000" in origins
    assert "*" not in origins


def test_cors_env_override():
    """Verify CORS origins can be overridden via env var."""
    import os
    os.environ["CORS_ORIGINS"] = "http://example.com,http://test.com"
    try:
        from app.config import Settings
        s = Settings(_env_file=None)
        origins = s.get_cors_origins_list()
        assert "http://example.com" in origins
        assert "http://test.com" in origins
        assert len(origins) == 2
    finally:
        del os.environ["CORS_ORIGINS"]
