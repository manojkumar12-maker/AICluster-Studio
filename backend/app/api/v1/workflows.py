from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...database import get_db
from ...models.workflow import Workflow, WorkflowTask, Artifact
from ...workflow.executor.engine import WorkflowEngine
from ...workflow.planner.service import WorkflowPlanner
from ...workflow.dispatcher.service import TaskDispatcher
from ...workflow.artifacts.service import ArtifactStore
from ...workflow.cache.service import CacheService
from ...workflow.metrics.service import MetricsService
from ...websocket.manager import ws_manager

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("")
async def create_workflow(data: dict, db: AsyncSession = Depends(get_db)):
    engine = WorkflowEngine(db)
    wf = await engine.create_workflow(
        name=data.get("name", "Untitled"),
        tasks_config=data.get("tasks", []),
        workflow_type=data.get("type", "custom"),
        priority=data.get("priority", 2),
        config=data.get("config"),
        created_by=data.get("created_by"),
    )
    return {"id": wf.id, "name": wf.name, "status": wf.status, "total_tasks": wf.total_tasks}


@router.get("")
async def list_workflows(status: Optional[str] = None, limit: int = 50, db: AsyncSession = Depends(get_db)):
    query = select(Workflow).order_by(Workflow.created_at.desc()).limit(limit)
    if status:
        query = query.where(Workflow.status == status)
    result = await db.execute(query)
    workflows = result.scalars().all()
    return [{"id": w.id, "name": w.name, "status": w.status, "type": w.workflow_type,
             "progress": w.progress, "total_tasks": w.total_tasks, "completed": w.completed_tasks,
             "failed": w.failed_tasks, "created_at": w.created_at.isoformat()} for w in workflows]


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(404, "Workflow not found")
    result = await db.execute(select(WorkflowTask).where(WorkflowTask.workflow_id == workflow_id).order_by(WorkflowTask.position))
    tasks = result.scalars().all()
    planner = WorkflowPlanner(db)
    dag = await planner.generate_dag(tasks)
    return {
        "id": wf.id, "name": wf.name, "description": wf.description, "status": wf.status,
        "type": wf.workflow_type, "priority": wf.priority, "progress": wf.progress,
        "total_tasks": wf.total_tasks, "completed_tasks": wf.completed_tasks,
        "failed_tasks": wf.failed_tasks, "estimated_duration": wf.estimated_duration_seconds,
        "created_at": wf.created_at.isoformat(), "started_at": wf.started_at.isoformat() if wf.started_at else None,
        "finished_at": wf.finished_at.isoformat() if wf.finished_at else None,
        "tasks": [{"id": t.id, "name": t.name, "type": t.task_type, "status": t.status,
                    "position": t.position, "assigned_worker": t.assigned_worker,
                    "retry_count": t.retry_count, "duration_ms": t.duration_ms,
                    "error": t.error} for t in tasks],
        "dag": dag,
    }


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    engine = WorkflowEngine(db)
    success = await engine.cancel_workflow(workflow_id)
    if not success:
        raise HTTPException(404, "Workflow not found")
    return {"status": "cancelled"}


@router.post("/{workflow_id}/pause")
async def pause_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(404, "Workflow not found")
    wf.status = "WAITING"
    await db.commit()
    return {"status": "paused"}


@router.post("/{workflow_id}/resume")
async def resume_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(404, "Workflow not found")
    wf.status = "QUEUED"
    await db.commit()
    return {"status": "resumed"}


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    engine = WorkflowEngine(db)
    success = await engine.cancel_workflow(workflow_id)
    if not success:
        raise HTTPException(404, "Workflow not found")
    return {"status": "cancelled"}


@router.get("/{workflow_id}/tasks")
async def get_workflow_tasks(workflow_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkflowTask).where(WorkflowTask.workflow_id == workflow_id).order_by(WorkflowTask.position))
    tasks = result.scalars().all()
    return [{"id": t.id, "name": t.name, "type": t.task_type, "status": t.status,
             "assigned_worker": t.assigned_worker, "retry_count": t.retry_count,
             "duration_ms": t.duration_ms, "position": t.position, "error": t.error,
             "created_at": t.created_at.isoformat()} for t in tasks]


@router.get("/{workflow_id}/artifacts")
async def get_workflow_artifacts(workflow_id: str, db: AsyncSession = Depends(get_db)):
    store = ArtifactStore(db)
    artifacts = await store.get_by_workflow(workflow_id)
    return [{"id": a.id, "name": a.name, "type": a.type, "size_bytes": a.size_bytes,
             "task_id": a.task_id, "worker_id": a.worker_id, "created_at": a.created_at.isoformat()} for a in artifacts]


@router.get("/{workflow_id}/metrics")
async def get_workflow_metrics(workflow_id: str, db: AsyncSession = Depends(get_db)):
    metrics = MetricsService(db)
    data = await metrics.get_workflow_metrics(workflow_id)
    queue = await metrics.get_queue_stats()
    return {"workflow_metrics": data, "queue_stats": queue}


@router.get("/queue")
async def get_queue(db: AsyncSession = Depends(get_db)):
    metrics = MetricsService(db)
    return await metrics.get_queue_stats()


@router.get("/history")
async def get_workflow_history(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).order_by(Workflow.created_at.desc()).limit(limit))
    workflows = result.scalars().all()
    return [{"id": w.id, "name": w.name, "status": w.status, "type": w.workflow_type,
             "progress": w.progress, "total_tasks": w.total_tasks, "duration_ms": (
                 (w.finished_at - w.started_at).total_seconds() * 1000 if w.finished_at and w.started_at else None
             ), "created_at": w.created_at.isoformat()} for w in workflows]


@router.get("/workers/capabilities")
async def get_worker_capabilities(db: AsyncSession = Depends(get_db)):
    from ...models.workflow import WorkerCapability
    result = await db.execute(select(WorkerCapability))
    caps = result.scalars().all()
    return [{"worker_id": c.worker_id, "supported_tasks": c.supported_tasks,
             "cpu_cores": c.cpu_cores, "ram_gb": c.ram_gb, "os": c.os,
             "python_version": c.python_version, "tools": c.tools} for c in caps]
