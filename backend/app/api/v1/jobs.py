from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.scheduler import SchedulerService
from ...websocket.manager import ws_manager
from ...schemas import JobCreateRequest, JobResponse

router = APIRouter(tags=["jobs"])


@router.post("/jobs", response_model=JobResponse)
async def create_job(data: JobCreateRequest, db: AsyncSession = Depends(get_db)):
    scheduler = SchedulerService(db)
    job = await scheduler.create_job(
        job_type=data.type, payload=data.payload, priority=data.priority
    )
    await ws_manager.broadcast_job_update({
        "id": job.id,
        "type": job.type,
        "status": job.status,
        "event": "created",
    })
    return JobResponse(
        id=job.id,
        type=job.type,
        status=job.status,
        assigned_worker=job.assigned_worker,
        progress=job.progress,
        priority=job.priority,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    scheduler = SchedulerService(db)
    jobs = await scheduler.get_all()
    return [
        JobResponse(
            id=j.id, type=j.type, status=j.status,
            assigned_worker=j.assigned_worker, progress=j.progress,
            priority=j.priority, error=j.error,
            created_at=j.created_at, started_at=j.started_at,
            finished_at=j.finished_at,
        )
        for j in jobs
    ]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    scheduler = SchedulerService(db)
    job = await scheduler.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(
        id=job.id, type=job.type, status=job.status,
        assigned_worker=job.assigned_worker, progress=job.progress,
        priority=job.priority, error=job.error,
        created_at=job.created_at, started_at=job.started_at,
        finished_at=job.finished_at,
    )


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_db)):
    scheduler = SchedulerService(db)
    try:
        job = await scheduler.cancel_job(job_id)
        await ws_manager.broadcast_job_update({
            "id": job.id, "status": job.status, "event": "cancelled",
        })
        return {"status": "cancelled", "job_id": job.id}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
