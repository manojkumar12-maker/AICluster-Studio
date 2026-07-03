import logging
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.workflow import ExecutionMetric, Workflow, WorkflowTask

logger = logging.getLogger(__name__)


class MetricsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record(self, workflow_id: str, metric_type: str, value: float,
                     unit: str = "ms", task_id: str | None = None, worker_id: str | None = None):
        metric = ExecutionMetric(
            workflow_id=workflow_id, task_id=task_id, worker_id=worker_id,
            metric_type=metric_type, value=value, unit=unit,
        )
        self.db.add(metric)
        await self.db.commit()

    async def get_workflow_metrics(self, workflow_id: str) -> dict:
        result = await self.db.execute(
            select(ExecutionMetric).where(ExecutionMetric.workflow_id == workflow_id)
        )
        metrics = result.scalars().all()
        summary: dict[str, float] = {}
        for m in metrics:
            key = m.metric_type
            summary[key] = summary.get(key, 0) + m.value
        return summary

    async def get_queue_stats(self) -> dict:
        result = await self.db.execute(select(func.count(Workflow.id)).where(Workflow.status == "QUEUED"))
        queued_wf = result.scalar() or 0
        result = await self.db.execute(select(func.count(WorkflowTask.id)).where(WorkflowTask.status == "READY"))
        ready = result.scalar() or 0
        result = await self.db.execute(select(func.count(WorkflowTask.id)).where(WorkflowTask.status == "RUNNING"))
        running = result.scalar() or 0
        result = await self.db.execute(select(func.count(WorkflowTask.id)).where(WorkflowTask.status == "RETRY"))
        retrying = result.scalar() or 0
        return {"queued_workflows": queued_wf, "ready_tasks": ready, "running_tasks": running, "retrying_tasks": retrying}

    async def get_worker_utilization(self) -> list[dict]:
        result = await self.db.execute(
            select(WorkflowTask.assigned_worker, func.count(WorkflowTask.id))
            .where(WorkflowTask.status.in_(["RUNNING", "ASSIGNED"]))
            .group_by(WorkflowTask.assigned_worker)
        )
        return [{"worker_id": row[0], "active_tasks": row[1]} for row in result if row[0]]
