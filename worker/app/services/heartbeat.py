import asyncio
import logging

import psutil

from ..config import settings
from ..core.constants import HEARTBEAT_INTERVAL
from ..utils.http_client import WorkerHttpClient

logger = logging.getLogger(__name__)


class HeartbeatService:
    def __init__(self, worker_id: str, http_client: WorkerHttpClient):
        self.worker_id = worker_id
        self.http_client = http_client
        self._running = False

    async def start(self):
        self._running = True
        asyncio.create_task(self._heartbeat_loop())

    async def stop(self):
        self._running = False

    async def _heartbeat_loop(self):
        while self._running:
            try:
                await self._send_heartbeat()
            except Exception as e:
                logger.error(
                    f"Heartbeat error: {e}",
                    extra={"worker_id": self.worker_id},
                )
            await asyncio.sleep(settings.heartbeat_interval)

    async def _send_heartbeat(self):
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()

        payload = {
            "id": self.worker_id,
            "cpu": round(cpu, 1),
            "ram": round(mem.percent, 1),
            "disk": round(disk.percent, 1),
            "temperature": None,
            "busy": False,
            "network_speed": round((net.bytes_sent + net.bytes_recv) / 1024, 1),
            "version": "1.0.0",
        }

        try:
            response = await self.http_client.post(
                "/workers/heartbeat", json=payload
            )
            if response.status_code == 200:
                logger.debug(
                    "Heartbeat sent: CPU=%.1f%% RAM=%.1f%%",
                    cpu,
                    mem.percent,
                    extra={"worker_id": self.worker_id},
                )
            else:
                logger.warning(
                    f"Heartbeat failed: {response.status_code}",
                    extra={"worker_id": self.worker_id},
                )
        except Exception as e:
            logger.warning(
                f"Heartbeat connection error: {e}",
                extra={"worker_id": self.worker_id},
            )
