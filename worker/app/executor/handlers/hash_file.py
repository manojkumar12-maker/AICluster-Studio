import asyncio
import hashlib

from ..base import BaseJobHandler


class HashFileHandler(BaseJobHandler):
    async def execute(self, job_id: str, payload: dict) -> dict:
        filepath = payload.get("filepath", "")
        algorithm = payload.get("algorithm", "sha256")

        if not filepath:
            return {"error": "filepath required", "job_id": job_id, "handler": "hash_file"}

        try:
            result = await asyncio.to_thread(self._hash_sync, filepath, algorithm, job_id)
            return result
        except Exception as e:
            return {"error": str(e), "job_id": job_id, "handler": "hash_file"}

    @staticmethod
    def _hash_sync(filepath: str, algorithm: str, job_id: str) -> dict:
        h = hashlib.new(algorithm)
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return {
            "filepath": filepath,
            "algorithm": algorithm,
            "hash": h.hexdigest(),
            "job_id": job_id,
            "handler": "hash_file",
        }
