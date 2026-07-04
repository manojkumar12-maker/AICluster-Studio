import json
import logging
import os
import socket
import secrets
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


def load_json_config() -> dict:
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


json_config = load_json_config()


class WorkerSettings(BaseSettings):
    master_url: str = json_config.get("master_url", "http://localhost:8000")
    worker_host: str = "0.0.0.0"
    worker_port: int = json_config.get("worker_port", 8001)
    worker_name: str = json_config.get("worker_name", "")
    worker_secret: str = json_config.get("worker_secret", "")
    cpu_limit: float = json_config.get("cpu_limit", 25.0)
    ram_limit_gb: float = json_config.get("ram_limit_gb", 8.0)
    heartbeat_interval: int = json_config.get("heartbeat_interval", 5)
    poll_interval: int = json_config.get("poll_interval", 5)
    log_level: str = json_config.get("log_level", "INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.worker_secret:
            env_secret = os.environ.get("AICLUSTER_MASTER_SECRET")
            if env_secret:
                self.worker_secret = env_secret
                worker_config = dict(json_config)
                worker_config["worker_secret"] = env_secret
                try:
                    with open(CONFIG_FILE, "w") as f:
                        json.dump(worker_config, f, indent=2)
                except OSError:
                    pass

    def get_worker_name(self) -> str:
        return self.worker_name or socket.gethostname()

    def get_ip_address(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"


settings = WorkerSettings()
