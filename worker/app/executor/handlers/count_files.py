import os

from ..base import BaseJobHandler


class CountFilesHandler(BaseJobHandler):
    async def execute(self, job_id: str, payload: dict) -> dict:
        directory = payload.get("directory", ".")
        pattern = payload.get("pattern", None)
        count = 0
        total_size = 0

        try:
            for root, dirs, files in os.walk(directory):
                for fname in files:
                    if pattern and pattern not in fname:
                        continue
                    count += 1
                    try:
                        total_size += os.path.getsize(os.path.join(root, fname))
                    except OSError:
                        pass
        except Exception as e:
            return {
                "error": str(e),
                "job_id": job_id,
                "handler": "count_files",
            }

        return {
            "directory": directory,
            "pattern": pattern,
            "file_count": count,
            "total_size_bytes": total_size,
            "job_id": job_id,
            "handler": "count_files",
        }
