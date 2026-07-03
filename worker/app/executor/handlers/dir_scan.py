import os

from ..base import BaseJobHandler


class DirectoryScanHandler(BaseJobHandler):
    async def execute(self, job_id: str, payload: dict) -> dict:
        directory = payload.get("directory", ".")
        results = []
        total_size = 0
        file_count = 0
        dir_count = 0

        try:
            for root, dirs, files in os.walk(directory):
                dir_count += len(dirs)
                for fname in files:
                    file_count += 1
                    fpath = os.path.join(root, fname)
                    try:
                        total_size += os.path.getsize(fpath)
                    except OSError:
                        pass
                if file_count > 10000:
                    break
        except Exception as e:
            return {
                "error": str(e),
                "job_id": job_id,
                "handler": "dir_scan",
            }

        return {
            "directory": directory,
            "file_count": file_count,
            "dir_count": dir_count,
            "total_size_bytes": total_size,
            "job_id": job_id,
            "handler": "dir_scan",
        }
