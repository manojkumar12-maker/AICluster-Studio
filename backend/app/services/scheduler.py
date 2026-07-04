import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models.job import Job
from ..models.worker import Worker
from ..models.log import SystemLog

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        self._stop_event.clear()
        self._task = asyncio.create_task(self._scheduler_loop())

    async def stop(self):
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _scheduler_loop(self):
        while not self._stop_event.is_set():
            try:
                await self._process_queue()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=2)
            except asyncio.TimeoutError:
                pass

    async def _process_queue(self):
        queued_result = await self.db.execute(
            select(Job)
            .where(Job.status == "queued")
            .order_by(Job.priority.desc(), Job.created_at.asc())
        )
        queued_jobs = queued_result.scalars().all()

        for job in queued_jobs:
            worker = await self._find_available_worker(job)
            if worker:
                await self._assign_job(job, worker)

    async def _find_available_worker(self, job: Job) -> Optional[Worker]:
        if job.assigned_worker:
            result = await self.db.execute(
                select(Worker).where(
                    Worker.id == job.assigned_worker,
                    Worker.status.in_(["online", "busy"]),
                    Worker.is_paused == False,
                )
            )
            return result.scalar_one_or_none()

        result = await self.db.execute(
            select(Worker)
            .where(Worker.status == "online", Worker.is_paused == False)
            .order_by(Worker.cpu_percent.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _assign_job(self, job: Job, worker: Worker):
        job.status = "running"
        job.assigned_worker = worker.id
        job.started_at = datetime.now(timezone.utc)
        worker.status = "busy"
        worker.current_job = job.id
        await self.db.commit()
        logger.info(f"Assigned job {job.id} to worker {worker.worker_name}")

    async def create_job(
        self, job_type: str = "custom", payload: dict | None = None,
        priority: int = 2
    ) -> Job:
        job_payload: dict = payload if payload is not None else {}
        job = Job(
            type=job_type,
            status="queued",
            payload=job_payload,
            priority=priority,
        )
        self.db.add(job)

        log = SystemLog(
            level="INFO",
            message=f"Job '{job.id}' created (type: {job_type}, priority: {priority})",
            source="scheduler",
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def cancel_job(self, job_id: str) -> Job:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError("Job not found")
        if job.status in ("completed", "failed", "cancelled"):
            raise ValueError("Job already finished")

        job.status = "cancelled"
        job.finished_at = datetime.now(timezone.utc)

        if job.assigned_worker:
            w_result = await self.db.execute(
                select(Worker).where(Worker.id == job.assigned_worker)
            )
            worker = w_result.scalar_one_or_none()
            if worker:
                worker.status = "online"
                worker.current_job = None

        log = SystemLog(
            level="INFO",
            message=f"Job '{job.id}' cancelled",
            source="scheduler",
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_all(self) -> list[Job]:
        result = await self.db.execute(
            select(Job).order_by(Job.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, job_id: str) -> Job | None:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def update_progress(self, job_id: str, progress: float):
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            job.progress = progress
            await self.db.commit()

    async def get_next_for_worker(self, worker_id: str) -> Job | None:
        result = await self.db.execute(
            select(Job)
            .where(Job.status == "queued")
            .order_by(Job.priority.desc(), Job.created_at.asc())
            .limit(1)
        )
        job = result.scalar_one_or_none()
        if job:
            job.status = "running"
            job.assigned_worker = worker_id
            job.started_at = datetime.now(timezone.utc)
            w_result = await self.db.execute(
                select(Worker).where(Worker.id == worker_id)
            )
            worker = w_result.scalar_one_or_none()
            if worker:
                worker.status = "busy"
                worker.current_job = job.id
            log = SystemLog(
                level="INFO",
                message=f"Job '{job.id}' assigned to worker '{worker_id}'",
                source="scheduler",
            )
            self.db.add(log)
            await self.db.commit()
            await self.db.refresh(job)
        return job

    async def complete_job(
        self, job_id: str, status: str, result_data: dict | None = None,
        error: str | None = None, duration_ms: float | None = None,
    ) -> Job | None:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return None
        job.status = status
        job.finished_at = datetime.now(timezone.utc)
        if result_data is not None:
            job.result = result_data
        if error is not None:
            job.error = error
        if duration_ms is not None:
            job.duration_ms = duration_ms
        if job.assigned_worker:
            w_result = await self.db.execute(
                select(Worker).where(Worker.id == job.assigned_worker)
            )
            worker = w_result.scalar_one_or_none()
            if worker:
                worker.status = "online"
                worker.current_job = None
        log = SystemLog(
            level="INFO" if status == "completed" else "WARNING",
            message=f"Job '{job.id}' {status}",
            source="scheduler",
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_running_count(self) -> int:
        return await self.db.scalar(
            select(func.count(Job.id)).where(Job.status == "running")
        ) or 0
