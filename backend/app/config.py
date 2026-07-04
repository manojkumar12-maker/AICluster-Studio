import logging
import os
import secrets

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    app_name: str = "AICluster"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "sqlite+aiosqlite:///./data/aicluster.db"
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    worker_timeout_seconds: int = 15
    max_workers: int = 100
    max_queued_jobs: int = 1000
    heartbeat_interval: int = 5

    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    data_dir: str = "data"
    logs_dir: str = "logs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.secret_key = self._load_secret()

    def _load_secret(self) -> str:
        env_secret = os.environ.get("AICLUSTER_SECRET_KEY")
        if env_secret:
            return env_secret

        secret_file = os.path.join(self.data_dir, "secret.key")
        if os.path.exists(secret_file):
            with open(secret_file, "r") as f:
                return f.read().strip()

        new_secret = secrets.token_hex(32)
        os.makedirs(self.data_dir, exist_ok=True)
        with open(secret_file, "w") as f:
            f.write(new_secret)
        logger.info("Generated new JWT secret key in %s", secret_file)
        return new_secret

    def get_cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
os.makedirs(settings.data_dir, exist_ok=True)
os.makedirs(settings.logs_dir, exist_ok=True)
