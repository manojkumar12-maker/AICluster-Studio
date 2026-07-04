import os
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport

# Set a known admin password for tests
os.environ.setdefault("AICLUSTER_ADMIN_PASSWORD", "TestAdminPass123!")

_test_db_file = os.path.join(tempfile.gettempdir(), "aicluster_test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_test_db_file}"

from app.database import Base, get_engine, get_session_factory
from app.models.worker import Worker
from app.models.job import Job
from app.models.log import SystemLog
from app.models.user import User
from app.services.auth import AuthService


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def admin_password():
    return os.environ.get("AICLUSTER_ADMIN_PASSWORD", "TestAdminPass123!")


@pytest.fixture(autouse=True)
async def setup_db(admin_password):
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = get_session_factory()
    async with factory() as session:
        auth = AuthService(session)
        await auth.seed_default_admin()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def auth_token(admin_password):
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": admin_password},
        )
        if resp.status_code == 200:
            return resp.json()["access_token"]
        return None


@pytest.fixture
async def client(auth_token):
    from app.main import app
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac


@pytest.fixture
async def db_session():
    factory = get_session_factory()
    async with factory() as session:
        yield session


def pytest_sessionfinish(session):
    if os.path.exists(_test_db_file):
        os.remove(_test_db_file)
