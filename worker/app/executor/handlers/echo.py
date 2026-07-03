from ..base import BaseJobHandler


class EchoJobHandler(BaseJobHandler):
    async def execute(self, job_id: str, payload: dict) -> dict:
        return {
            "echo": payload,
            "job_id": job_id,
            "handler": "echo",
        }
