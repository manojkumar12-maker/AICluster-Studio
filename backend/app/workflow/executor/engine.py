import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.workflow import Workflow, WorkflowTask, TaskDependency, WorkflowResult, WorkflowEvent
from ...websocket.manager import ws_manager
from ..state.states import is_valid_task_transition, TASK_TYPES
from ..planner.service import WorkflowPlanner
from ..dispatcher.service import TaskDispatcher
from ..artifacts.service import ArtifactStore
from ..cache.service import CacheService
from ..metrics.service import MetricsService

logger = logging.getLogger(__name__)

RETRY_DELAYS = [5, 30, 60]
RETRY_EVENT_TYPES = {
    "task_assigned": "ASSIGNED", "task_started": "RUNNING",
    "task_progress": "RUNNING", "task_finished": "SUCCESS",
    "task_failed": "FAILED", "workflow_finished": "COMPLETED",
    "workflow_failed": "FAILED",
}


class WorkflowEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.planner = WorkflowPlanner(db)
        self.dispatcher = TaskDispatcher(db)
        self.artifact_store = ArtifactStore(db)
        self.cache = CacheService(db)
        self.metrics = MetricsService(db)

    async def create_workflow(self, name: str, tasks_config: list[dict],
                               workflow_type: str = "custom", priority: int = 2,
                               config: dict | None = None, created_by: str | None = None) -> Workflow:
        wf = Workflow(
            name=name, workflow_type=workflow_type, priority=priority,
            config=config or {}, created_by=created_by, status="PENDING",
        )
        self.db.add(wf)
        await self.db.commit()
        await self.db.refresh(wf)

        wf.status = "PLANNING"
        await self.db.commit()
        planned = await self.planner.plan(wf, tasks_config)
        wf.estimated_duration_seconds = await self.planner.estimate_duration(planned)

        wf.status = "QUEUED"
        await self.db.commit()
        await self._broadcast("workflow_created", {"id": wf.id, "name": wf.name, "status": wf.status})

        logger.info(f"Workflow {wf.id} created with {len(planned)} tasks")
        return wf

    async def dispatch_workflow(self, workflow_id: str) -> bool:
        wf = await self.db.get(Workflow, workflow_id)
        if not wf:
            return False
        wf.status = "DISPATCHING"
        wf.started_at = datetime.now(timezone.utc)
        await self.db.commit()

        result = await self.db.execute(
            select(WorkflowTask).where(
                WorkflowTask.workflow_id == workflow_id,
                WorkflowTask.status == "CREATED",
            ).order_by(WorkflowTask.position)
        )
        tasks = list(result.scalars().all())

        for task in tasks:
            dep_check = await self.db.execute(
                select(TaskDependency).where(TaskDependency.task_id == task.id)
            )
            deps = dep_check.scalars().all()
            if deps:
                task.status = "WAITING"
            else:
                task.status = "READY"

        await self.db.commit()
        await self._broadcast("workflow_dispatching", {"id": workflow_id, "tasks": len(tasks)})
        return True

    async def assign_and_execute(self, task_id: str) -> bool:
        task = await self.db.get(WorkflowTask, task_id)
        if not task or task.status != "READY":
            return False
        worker_id = await self.dispatcher.dispatch(task)
        if not worker_id:
            task.status = "WAITING"
            await self.db.commit()
            return False
        await self._broadcast("task_assigned", {"task_id": task_id, "worker_id": worker_id, "workflow_id": task.workflow_id})
        return True

    async def complete_task(self, task_id: str, result: dict | None = None,
                            error: str | None = None, duration_ms: float | None = None,
                            status: str = "SUCCESS") -> WorkflowTask | None:
        task = await self.db.get(WorkflowTask, task_id)
        if not task:
            return None

        task.status = status
        task.result = result
        task.error = error
        task.duration_ms = duration_ms
        task.finished_at = datetime.now(timezone.utc)
        await self.db.commit()

        wf = await self.db.get(Workflow, task.workflow_id)
        if wf:
            if status == "SUCCESS":
                wf.completed_tasks += 1
            else:
                wf.failed_tasks += 1
            total = max(wf.total_tasks, 1)
            wf.progress = round((wf.completed_tasks + wf.failed_tasks) / total * 100, 1)
            if wf.completed_tasks + wf.failed_tasks >= wf.total_tasks:
                wf.status = "MERGING" if wf.failed_tasks == 0 else "FAILED"
                wf.finished_at = datetime.now(timezone.utc)
                await self._broadcast("workflow_finished" if wf.status == "MERGING" else "workflow_failed",
                                      {"id": wf.id, "progress": wf.progress})
            await self.db.commit()

        await self._broadcast("task_finished", {"task_id": task_id, "status": status, "workflow_id": task.workflow_id})
        return task

    async def retry_task(self, task_id: str) -> bool:
        task = await self.db.get(WorkflowTask, task_id)
        if not task or task.status != "FAILED":
            return False
        if task.retry_count >= task.max_retries:
            return False
        delay = RETRY_DELAYS[min(task.retry_count, len(RETRY_DELAYS) - 1)]
        task.retry_count += 1
        task.status = "RETRY"
        await self.db.commit()
        await self._broadcast("task_retrying", {"task_id": task_id, "attempt": task.retry_count, "delay": delay})

        async def delayed_retry():
            await asyncio.sleep(delay)
            async for db in get_db():
                engine = WorkflowEngine(db)
                t = await db.get(WorkflowTask, task_id)
                if t:
                    t.status = "READY"
                    t.assigned_worker = None
                    await db.commit()
                    await engine.assign_and_execute(task_id)
                break

        asyncio.create_task(delayed_retry())
        return True

    async def cancel_workflow(self, workflow_id: str) -> bool:
        wf = await self.db.get(Workflow, workflow_id)
        if not wf:
            return False
        wf.status = "CANCELLED"
        wf.finished_at = datetime.now(timezone.utc)
        await self.db.commit()

        await self.db.execute(
            update(WorkflowTask).where(
                WorkflowTask.workflow_id == workflow_id,
                WorkflowTask.status.in_(["CREATED", "READY", "WAITING", "RETRY", "RUNNING"]),
            ).values(status="CANCELLED")
        )
        await self.db.commit()
        await self._broadcast("workflow_cancelled", {"id": workflow_id})
        logger.info(f"Workflow {workflow_id} cancelled")
        return True

    async def _broadcast(self, event_type: str, data: dict):
        try:
            await ws_manager.broadcast(f"workflow_{event_type}", data)
        except Exception as e:
            logger.warning(f"Broadcast error: {e}")
