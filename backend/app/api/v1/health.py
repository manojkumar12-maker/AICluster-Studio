from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.worker_manager import WorkerManagerService
from ...config import settings
from ...schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    wm = WorkerManagerService(db)
    worker_count = await wm.count()
    return HealthResponse(
        status="ok",
        database="connected",
        worker_count=worker_count,
        version=settings.app_version,
    )
