import pytest


class TestWorkerConfig:
    def test_config_defaults(self):
        from app.config import WorkerSettings

        settings = WorkerSettings(
            master_url="http://test:8000",
            worker_name="test-worker",
        )
        assert settings.master_url == "http://test:8000"
        assert settings.worker_name == "test-worker"
        assert settings.heartbeat_interval == 5
        assert settings.log_level == "INFO"

    def test_worker_name_fallback(self):
        from app.config import WorkerSettings
        import socket

        settings = WorkerSettings(master_url="http://test:8000", worker_name="")
        assert settings.get_worker_name() == socket.gethostname()

    def test_ip_address_resolution(self):
        from app.config import WorkerSettings

        settings = WorkerSettings(master_url="http://test:8000")
        ip = settings.get_ip_address()
        assert ip is not None
        assert len(ip) > 0
