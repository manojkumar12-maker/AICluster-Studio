import os
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport

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


@pytest.fixture(autouse=True)
async def setup_db():
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
async def client():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def pytest_sessionfinish(session):
    if os.path.exists(_test_db_file):
        os.remove(_test_db_file)
