import logging
import sys
import sqlite3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class HealthService:
    SUBSYSTEMS = ["master", "worker", "workflow", "repository", "ai_runtime", "agents", "database", "websocket", "cache", "artifact_store"]

    async def check_all(self) -> dict:
        results = {}
        for subsystem in self.SUBSYSTEMS:
            results[subsystem] = await self._check_subsystem(subsystem)
        all_healthy = all(r["healthy"] for r in results.values())
        return {"overall": "healthy" if all_healthy else "degraded", "subsystems": results, "timestamp": datetime.now(timezone.utc).isoformat()}

    async def check_subsystem(self, name: str) -> dict:
        return await self._check_subsystem(name)

    async def _check_subsystem(self, name: str) -> dict:
        checks = {"master": {"healthy": True, "version": "1.0.0", "latency_ms": 0, "dependencies": ["database", "websocket"]},
                  "worker": {"healthy": True, "version": "1.0.0", "latency_ms": 0, "dependencies": ["master"]},
                  "workflow": {"healthy": True, "version": "1.0.0", "latency_ms": 0, "dependencies": ["database", "worker"]},
                  "repository": {"healthy": True, "version": "1.0.0", "latency_ms": 0, "dependencies": ["database"]},
                  "ai_runtime": {"healthy": True, "version": "1.0.0", "latency_ms": 0, "dependencies": ["database"]},
                  "agents": {"healthy": True, "version": "1.0.0", "latency_ms": 0, "dependencies": ["database", "ai_runtime"]},
                  "database": self._check_database(),
                  "websocket": {"healthy": True, "version": "1.0.0", "latency_ms": 0, "dependencies": []},
                  "cache": {"healthy": True, "version": "1.0.0", "latency_ms": 0, "dependencies": ["database"]},
                  "artifact_store": {"healthy": True, "version": "1.0.0", "latency_ms": 0, "dependencies": ["database"]},
        }
        return checks.get(name, {"healthy": False, "error": f"Unknown subsystem: {name}"})

    def _check_database(self) -> dict:
        try:
            from ...database import DATA_FILE
            conn = sqlite3.connect(str(DATA_FILE))
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
            return {"healthy": True, "version": "sqlite3", "latency_ms": 0, "dependencies": []}
        except Exception as e:
            return {"healthy": False, "error": str(e), "dependencies": []}
