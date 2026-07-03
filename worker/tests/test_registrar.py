import pytest


class TestRegistrar:
    @pytest.mark.asyncio
    async def test_registration_failure_returns_none(self):
        from app.utils.http_client import WorkerHttpClient
        from app.services.registrar import Registrar

        client = WorkerHttpClient("http://localhost:1")
        registrar = Registrar(client)
        result = await registrar.register()
        assert result is None
        await client.close()

    @pytest.mark.asyncio
    async def test_registrar_initial_state(self):
        from app.utils.http_client import WorkerHttpClient
        from app.services.registrar import Registrar

        client = WorkerHttpClient("http://localhost:8000")
        registrar = Registrar(client)
        assert registrar.worker_id is None
        await client.close()
