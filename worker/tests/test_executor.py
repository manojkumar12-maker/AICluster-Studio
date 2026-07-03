import pytest


class TestExecutor:
    @pytest.mark.asyncio
    async def test_echo_handler(self):
        from app.executor.handlers.echo import EchoJobHandler

        handler = EchoJobHandler()
        result = await handler.execute("job-1", {"key": "value"})
        assert result["handler"] == "echo"
        assert result["echo"] == {"key": "value"}
        assert result["job_id"] == "job-1"

    @pytest.mark.asyncio
    async def test_sleep_handler(self):
        from app.executor.handlers.sleep import SleepJobHandler

        handler = SleepJobHandler()
        result = await handler.execute("job-2", {"duration": 0.01})
        assert result["handler"] == "sleep"
        assert result["slept_for"] == 0.01

    @pytest.mark.asyncio
    async def test_count_files_handler_nonexistent(self):
        from app.executor.handlers.count_files import CountFilesHandler

        handler = CountFilesHandler()
        result = await handler.execute("job-3", {"directory": "/nonexistent"})
        assert result["handler"] == "count_files"
        assert result["file_count"] == 0

    @pytest.mark.asyncio
    async def test_hash_file_handler_missing_path(self):
        from app.executor.handlers.hash_file import HashFileHandler

        handler = HashFileHandler()
        result = await handler.execute("job-4", {})
        assert result["handler"] == "hash_file"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_registry(self):
        from app.executor.registry import JobRegistry
        from app.executor.handlers.echo import EchoJobHandler

        registry = JobRegistry()
        registry.register("echo", EchoJobHandler())

        handler = registry.get_handler("echo")
        assert handler is not None

        missing = registry.get_handler("nonexistent")
        assert missing is None

        assert "echo" in registry.registered_types
