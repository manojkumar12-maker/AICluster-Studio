from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.worker_manager import WorkerManagerService
from ...services.scheduler import SchedulerService
from ...websocket.manager import ws_manager
from ...schemas import (
    WorkerRegisterRequest,
    WorkerRegisterResponse,
    HeartbeatRequest,
    WorkerResponse,
    ProgressRequest,
    ResultRequest,
    NextJobResponse,
    JobResponse,
)

router = APIRouter(tags=["workers"])


@router.post("/workers/register", response_model=WorkerRegisterResponse)
async def register_worker(data: WorkerRegisterRequest, db: AsyncSession = Depends(get_db)):
    manager = WorkerManagerService(db)
    try:
        worker = await manager.register(
            name=data.name, hostname=data.hostname, ip=data.ip
        )
        await ws_manager.broadcast_worker_update({
            "id": worker.id,
            "worker_name": worker.worker_name,
            "status": worker.status,
            "event": "registered",
        })
        return WorkerRegisterResponse(id=worker.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workers/heartbeat")
async def worker_heartbeat(data: HeartbeatRequest, db: AsyncSession = Depends(get_db)):
    manager = WorkerManagerService(db)
    try:
        worker = await manager.process_heartbeat(
            worker_id=data.id,
            cpu=data.cpu,
            ram=data.ram,
            disk=data.disk,
            temperature=data.temperature,
            busy=data.busy,
            network_speed=data.network_speed,
        )
        await ws_manager.broadcast_worker_update({
            "id": worker.id,
            "worker_name": worker.worker_name,
            "status": worker.status,
            "cpu_percent": worker.cpu_percent,
            "ram_percent": worker.ram_percent,
            "event": "heartbeat",
        })
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers", response_model=list[WorkerResponse])
async def list_workers(db: AsyncSession = Depends(get_db)):
    manager = WorkerManagerService(db)
    workers = await manager.get_all()
    return [
        WorkerResponse(
            id=w.id,
            worker_name=w.worker_name,
            hostname=w.hostname,
            ip=w.ip,
            status=w.status,
            cpu_percent=w.cpu_percent,
            ram_percent=w.ram_percent,
            disk_percent=w.disk_percent,
            temperature=w.temperature,
            network_speed=w.network_speed,
            current_job=w.current_job,
            version=w.version,
            cpu_limit=w.cpu_limit,
            ram_limit=w.ram_limit,
            priority=w.priority,
            is_paused=w.is_paused,
            last_seen=w.last_seen,
            registered_at=w.registered_at,
        )
        for w in workers
    ]


@router.get("/workers/{worker_id}", response_model=WorkerResponse)
async def get_worker(worker_id: str, db: AsyncSession = Depends(get_db)):
    manager = WorkerManagerService(db)
    worker = await manager.get_by_id(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return WorkerResponse(
        id=worker.id,
        worker_name=worker.worker_name,
        hostname=worker.hostname,
        ip=worker.ip,
        status=worker.status,
        cpu_percent=worker.cpu_percent,
        ram_percent=worker.ram_percent,
        disk_percent=worker.disk_percent,
        temperature=worker.temperature,
        network_speed=worker.network_speed,
        current_job=worker.current_job,
        version=worker.version,
        cpu_limit=worker.cpu_limit,
        ram_limit=worker.ram_limit,
        priority=worker.priority,
        is_paused=worker.is_paused,
        last_seen=worker.last_seen,
        registered_at=worker.registered_at,
    )


@router.post("/workers/{worker_id}/pause")
async def pause_worker(worker_id: str, db: AsyncSession = Depends(get_db)):
    manager = WorkerManagerService(db)
    try:
        worker = await manager.pause(worker_id)
        return {"status": "paused", "worker_id": worker.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/workers/{worker_id}/resume")
async def resume_worker(worker_id: str, db: AsyncSession = Depends(get_db)):
    manager = WorkerManagerService(db)
    try:
        worker = await manager.resume(worker_id)
        return {"status": "resumed", "worker_id": worker.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/workers/{worker_id}/next-job")
async def next_job(worker_id: str, db: AsyncSession = Depends(get_db)):
    manager = WorkerManagerService(db)
    worker = await manager.get_by_id(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    if worker.is_paused:
        raise HTTPException(status_code=429, detail="Worker is paused")
    scheduler = SchedulerService(db)
    job = await scheduler.get_next_for_worker(worker_id)
    if job is None:
        return Response(status_code=204)
    return NextJobResponse(
        job=JobResponse(
            id=job.id, type=job.type, status=job.status,
            assigned_worker=job.assigned_worker, progress=job.progress,
            priority=job.priority, error=job.error,
            created_at=job.created_at, started_at=job.started_at,
            finished_at=job.finished_at,
        )
    )


@router.post("/workers/{worker_id}/progress")
async def report_progress(
    worker_id: str, data: ProgressRequest, db: AsyncSession = Depends(get_db),
):
    manager = WorkerManagerService(db)
    worker = await manager.get_by_id(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    scheduler = SchedulerService(db)
    await scheduler.update_progress(data.job_id, data.progress)
    await ws_manager.broadcast_job_update({
        "id": data.job_id,
        "progress": data.progress,
        "event": "progress",
    })
    return {"status": "ok"}


@router.post("/workers/{worker_id}/result")
async def report_result(
    worker_id: str, data: ResultRequest, db: AsyncSession = Depends(get_db),
):
    manager = WorkerManagerService(db)
    worker = await manager.get_by_id(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    scheduler = SchedulerService(db)
    job = await scheduler.complete_job(
        job_id=data.job_id, status=data.status,
        result_data=data.result, error=data.error,
        duration_ms=data.duration_ms,
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    await ws_manager.broadcast_job_update({
        "id": data.job_id,
        "status": data.status,
        "event": "result",
    })
    return {"status": "ok"}
