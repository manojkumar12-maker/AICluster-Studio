import logging

import socket

from ..config import settings
from ..utils.http_client import WorkerHttpClient

logger = logging.getLogger(__name__)


class Registrar:
    def __init__(self, http_client: WorkerHttpClient):
        self.http_client = http_client
        self._worker_id: str | None = None

    @property
    def worker_id(self) -> str | None:
        return self._worker_id

    async def register(self) -> str | None:
        hostname = settings.get_worker_name()
        ip = self._get_ip_address()

        payload = {
            "name": hostname,
            "hostname": hostname,
            "ip": ip,
        }

        try:
            response = await self.http_client.post("/workers/register", json=payload)
            if response.status_code == 200:
                data = response.json()
                self._worker_id = data.get("id")
                logger.info(
                    f"Registered with master: {settings.master_url} (ID: {self._worker_id})",
                    extra={"worker_id": self._worker_id},
                )
                return self._worker_id
            else:
                logger.error(
                    f"Registration failed: {response.status_code} {response.text}"
                )
        except Exception as e:
            logger.error(f"Registration error: {e}")

        return None

    def _get_ip_address(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def clear(self):
        self._worker_id = None
