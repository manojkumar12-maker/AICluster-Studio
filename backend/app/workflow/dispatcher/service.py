import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.worker import Worker
from ...models.workflow import WorkflowTask, WorkerCapability
from ...database import get_db

logger = logging.getLogger(__name__)


class TaskDispatcher:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def dispatch(self, task: WorkflowTask) -> str | None:
        workers = await self._find_candidates(task)
        if not workers:
            logger.warning(f"No available workers for task {task.id}")
            return None
        worker = workers[0]
        task.status = "ASSIGNED"
        task.assigned_worker = worker.id
        task.started_at = datetime.now(timezone.utc)
        await self.db.commit()
        logger.info(f"Task {task.id} ({task.task_type}) dispatched to worker {worker.worker_name}")
        return worker.id

    async def _find_candidates(self, task: WorkflowTask) -> list[Worker]:
        result = await self.db.execute(
            select(Worker)
            .where(Worker.status.in_(["online", "busy"]))
            .where(Worker.is_paused == False)
            .order_by(Worker.cpu_percent.asc(), Worker.priority.desc())
        )
        workers = list(result.scalars().all())
        if task.task_type in ("hash_file", "compress", "extract"):
            workers = [w for w in workers if w.cpu_percent < 70]
        return workers

    async def requeue(self, task_id: str) -> bool:
        result = await self.db.execute(select(WorkflowTask).where(WorkflowTask.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return False
        if task.retry_count >= task.max_retries:
            task.status = "FAILED"
            await self.db.commit()
            return False
        task.retry_count += 1
        task.status = "RETRY"
        task.assigned_worker = None
        await self.db.commit()
        logger.info(f"Task {task_id} requeued (attempt {task.retry_count}/{task.max_retries})")
        return True

    async def get_ready_tasks(self, workflow_id: str | None = None) -> list[WorkflowTask]:
        from ...models.workflow import TaskDependency
        query = select(WorkflowTask).where(WorkflowTask.status == "WAITING")
        if workflow_id:
            query = query.where(WorkflowTask.workflow_id == workflow_id)
        result = await self.db.execute(query.order_by(WorkflowTask.priority.desc(), WorkflowTask.position.asc()))
        tasks = list(result.scalars().all())
        ready = []
        for task in tasks:
            dep_result = await self.db.execute(
                select(TaskDependency).where(TaskDependency.task_id == task.id)
            )
            deps = dep_result.scalars().all()
            all_done = True
            for dep in deps:
                dep_task = await self.db.get(WorkflowTask, dep.depends_on_id)
                if dep_task and dep_task.status != "SUCCESS":
                    all_done = False
                    break
            if all_done:
                task.status = "READY"
                ready.append(task)
        if ready:
            await self.db.commit()
        return ready

    async def get_next_ready_task(self, worker_id: str) -> WorkflowTask | None:
        result = await self.db.execute(
            select(WorkflowTask)
            .where(WorkflowTask.status == "READY")
            .order_by(WorkflowTask.priority.desc(), WorkflowTask.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()
