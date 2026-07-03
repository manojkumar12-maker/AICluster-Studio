import logging

from ..utils.http_client import WorkerHttpClient

logger = logging.getLogger(__name__)


class Reporter:
    def __init__(self, worker_id: str, http_client: WorkerHttpClient):
        self.worker_id = worker_id
        self.http_client = http_client

    async def report_progress(
        self, job_id: str, progress: float, logs: str | None = None
    ) -> bool:
        payload = {
            "job_id": job_id,
            "progress": min(progress, 100.0),
        }
        if logs:
            payload["logs"] = logs

        try:
            response = await self.http_client.post(
                f"/workers/{self.worker_id}/progress",
                json=payload,
            )
            if response.status_code == 200:
                logger.debug(
                    f"Progress {progress:.0f}% reported for job {job_id}",
                    extra={"worker_id": self.worker_id, "job_id": job_id},
                )
                return True
            else:
                logger.warning(
                    f"Progress report failed: {response.status_code}",
                    extra={"worker_id": self.worker_id, "job_id": job_id},
                )
                return False
        except Exception as e:
            logger.error(
                f"Progress report error: {e}",
                extra={"worker_id": self.worker_id, "job_id": job_id},
            )
            return False

    async def report_result(
        self,
        job_id: str,
        status: str,
        result: dict | None = None,
        error: str | None = None,
        duration_ms: float | None = None,
        logs: str | None = None,
    ) -> bool:
        payload = {
            "job_id": job_id,
            "status": status,
        }
        if result is not None:
            payload["result"] = result
        if error is not None:
            payload["error"] = error
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        if logs is not None:
            payload["logs"] = logs

        try:
            response = await self.http_client.post(
                f"/workers/{self.worker_id}/result",
                json=payload,
            )
            if response.status_code == 200:
                logger.info(
                    f"Result reported for job {job_id}: {status}",
                    extra={"worker_id": self.worker_id, "job_id": job_id},
                )
                return True
            else:
                logger.warning(
                    f"Result report failed: {response.status_code}",
                    extra={"worker_id": self.worker_id, "job_id": job_id},
                )
                return False
        except Exception as e:
            logger.error(
                f"Result report error: {e}",
                extra={"worker_id": self.worker_id, "job_id": job_id},
            )
            return False
