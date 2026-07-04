import httpx
import logging

from ..core.constants import HTTP_TIMEOUT

logger = logging.getLogger(__name__)


class WorkerHttpClient:
    def __init__(self, master_url: str, worker_secret: str = "", timeout: int = HTTP_TIMEOUT):
        self.master_url = master_url.rstrip("/")
        self.worker_secret = worker_secret
        self._client = httpx.AsyncClient(timeout=timeout)

    def _get_headers(self) -> dict:
        headers = {}
        if self.worker_secret:
            headers["Authorization"] = f"Bearer {self.worker_secret}"
        return headers

    async def post(self, path: str, json: dict | None = None) -> httpx.Response:
        url = f"{self.master_url}/api/v1{path}"
        return await self._client.post(url, json=json, headers=self._get_headers())

    async def get(self, path: str) -> httpx.Response:
        url = f"{self.master_url}/api/v1{path}"
        return await self._client.get(url, headers=self._get_headers())

    async def close(self):
        await self._client.aclose()
