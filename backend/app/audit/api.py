import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from ..database import get_db
from .schemas import AuditSearchRequest, AuditStatistics, AuditSettingsResponse, AuditSettingsUpdate, AuditLogResponse
from .service import AuditService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
async def get_logs(
    limit: int = 100, offset: int = 0, category: str | None = None,
    severity: str | None = None, event_type: str | None = None,
    username: str | None = None, worker_id: str | None = None,
    workflow_id: str | None = None, repository_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = AuditService(db)
    req = AuditSearchRequest(limit=limit, offset=offset, category=category,
                              severity=severity, event_type=event_type, username=username,
                              worker_id=worker_id, workflow_id=workflow_id,
                              repository_id=repository_id)
    logs, total = await svc.search(req)
    return {"logs": [AuditLogResponse.model_validate(l).model_dump() for l in logs], "total": total, "limit": limit, "offset": offset}


@router.post("/search")
async def search_logs(req: AuditSearchRequest, db: AsyncSession = Depends(get_db)):
    svc = AuditService(db)
    logs, total = await svc.search(req)
    return {"logs": [AuditLogResponse.model_validate(l).model_dump() for l in logs], "total": total}


@router.get("/statistics", response_model=AuditStatistics)
async def get_statistics(db: AsyncSession = Depends(get_db)):
    svc = AuditService(db)
    return await svc.get_statistics()


@router.get("/categories")
async def get_categories():
    from .service import AuditService
    return {"categories": AuditService.CATEGORIES, "event_types": AuditService.EVENT_TYPES}


@router.get("/timeline")
async def get_timeline(limit: int = 50, db: AsyncSession = Depends(get_db)):
    svc = AuditService(db)
    req = AuditSearchRequest(limit=limit)
    logs, _ = await svc.search(req)
    return {"events": [AuditLogResponse.model_validate(l).model_dump() for l in logs]}


@router.post("/export")
async def export_logs(fmt: str = "csv", db: AsyncSession = Depends(get_db)):
    svc = AuditService(db)
    export = await svc.export_logs(fmt)
    return {"id": export.id, "filename": export.filename, "size_bytes": export.size_bytes, "record_count": export.record_count, "status": export.status}


@router.post("/purge")
async def purge_logs(days: int = 90, db: AsyncSession = Depends(get_db)):
    from datetime import timedelta, timezone
    svc = AuditService(db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    count = await svc.purge(cutoff)
    return {"purged": count, "before": cutoff.isoformat()}


@router.get("/settings", response_model=AuditSettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    svc = AuditService(db)
    return await svc.get_settings()


@router.post("/settings", response_model=AuditSettingsResponse)
async def update_settings(data: AuditSettingsUpdate, db: AsyncSession = Depends(get_db)):
    svc = AuditService(db)
    return await svc.update_settings(data.model_dump(exclude_none=True))
