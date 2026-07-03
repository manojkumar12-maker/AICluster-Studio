import asyncio
import logging

from ..config import settings
from ..core.constants import POLL_INTERVAL
from ..utils.http_client import WorkerHttpClient

logger = logging.getLogger(__name__)


class JobPoller:
    def __init__(self, worker_id: str, http_client: WorkerHttpClient):
        self.worker_id = worker_id
        self.http_client = http_client
        self._running = False

    async def start(self):
        self._running = True

    async def stop(self):
        self._running = False

    async def poll(self) -> dict | None:
        try:
            response = await self.http_client.get(
                f"/workers/{self.worker_id}/next-job"
            )

            if response.status_code == 200:
                data = response.json()
                job_data = data.get("job")
                if job_data:
                    logger.info(
                        f"Job received: {job_data.get('id')} type={job_data.get('type')}",
                        extra={"worker_id": self.worker_id, "job_id": job_data.get("id")},
                    )
                    return job_data
            elif response.status_code == 204:
                return None
            elif response.status_code == 404:
                logger.warning(
                    "Worker not found on master, may need re-registration",
                    extra={"worker_id": self.worker_id},
                )
                return None
            elif response.status_code == 429:
                retry_after = response.headers.get("retry-after", "10")
                wait = int(retry_after) if retry_after.isdigit() else 10
                logger.info(
                    f"Rate limited, waiting {wait}s",
                    extra={"worker_id": self.worker_id},
                )
                await asyncio.sleep(wait)
                return None
            else:
                logger.warning(
                    f"Job poll failed: {response.status_code}",
                    extra={"worker_id": self.worker_id},
                )
                return None

        except Exception as e:
            logger.error(
                f"Job poll error: {e}",
                extra={"worker_id": self.worker_id},
            )
            return None

        return None
