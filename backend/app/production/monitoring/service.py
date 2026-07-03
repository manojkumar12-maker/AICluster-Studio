import logging
import time
import psutil
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.worker import Worker
from ...models.workflow import Workflow, WorkflowTask
from ...websocket.manager import ws_manager

logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._start_time = time.time()

    async def get_system_metrics(self) -> dict:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "cpu_percent": round(cpu, 1), "ram_percent": round(mem.percent, 1),
            "ram_available_gb": round(mem.available / (1024**3), 1),
            "disk_percent": round(disk.percent, 1), "disk_free_gb": round(disk.free / (1024**3), 1),
            "uptime_seconds": round(time.time() - self._start_time),
        }

    async def get_cluster_metrics(self) -> dict:
        w = await self.db.execute(select(func.count(Worker.id)))
        total_workers = w.scalar() or 0
        w_online = await self.db.execute(select(func.count(Worker.id)).where(Worker.status == "online"))
        online = w_online.scalar() or 0
        wf_counts = await self.db.execute(select(Workflow.status, func.count(Workflow.id)).group_by(Workflow.status))
        workflows = {row.status: row[1] for row in wf_counts}
        t_counts = await self.db.execute(select(WorkflowTask.status, func.count(WorkflowTask.id)).group_by(WorkflowTask.status))
        tasks = {row.status: row[1] for row in t_counts}
        return {
            "total_workers": total_workers, "online_workers": online, "offline_workers": total_workers - online,
            "workflows": workflows, "tasks": tasks, "throughput": {"workflows_per_minute": 0, "tasks_per_minute": 0},
        }

    async def get_ai_metrics(self) -> dict:
        from ...models.ai import RuntimeMetric
        r = await self.db.execute(select(RuntimeMetric).order_by(RuntimeMetric.created_at.desc()).limit(50))
        metrics = r.scalars().all()
        return {"recent_metrics": [{"type": m.metric_type, "value": m.value, "unit": m.unit, "time": m.created_at.isoformat()} for m in metrics]}

    async def get_all_metrics(self) -> dict:
        return {"system": await self.get_system_metrics(), "cluster": await self.get_cluster_metrics(), "ai": await self.get_ai_metrics()}
