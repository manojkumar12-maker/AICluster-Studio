from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.log_service import LogService
from ...schemas import SystemLogResponse

router = APIRouter(tags=["logs"])


@router.get("/logs", response_model=list[SystemLogResponse])
async def get_logs(
    level: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = LogService(db)
    logs = await service.get_all(level=level, limit=limit, offset=offset)
    return [
        SystemLogResponse(
            id=log.id, level=log.level, message=log.message,
            source=log.source, created_at=log.created_at,
        )
        for log in logs
    ]
