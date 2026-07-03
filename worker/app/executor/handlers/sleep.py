import asyncio

from ..base import BaseJobHandler


class SleepJobHandler(BaseJobHandler):
    async def execute(self, job_id: str, payload: dict) -> dict:
        duration = payload.get("duration", 5)
        await asyncio.sleep(float(duration))
        return {
            "slept_for": duration,
            "job_id": job_id,
            "handler": "sleep",
        }
