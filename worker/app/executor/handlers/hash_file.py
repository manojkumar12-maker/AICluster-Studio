import hashlib

from ..base import BaseJobHandler


class HashFileHandler(BaseJobHandler):
    async def execute(self, job_id: str, payload: dict) -> dict:
        filepath = payload.get("filepath", "")
        algorithm = payload.get("algorithm", "sha256")

        if not filepath:
            return {"error": "filepath required", "job_id": job_id, "handler": "hash_file"}

        try:
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
        except Exception as e:
            return {
                "error": str(e),
                "job_id": job_id,
                "handler": "hash_file",
            }
