from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.worker_manager import WorkerManagerService
from ...services.scheduler import SchedulerService
from ...schemas import DashboardResponse

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    wm = WorkerManagerService(db)
    sc = SchedulerService(db)

    worker_stats = await wm.get_dashboard()
    running_jobs = await sc.get_running_count()

    return DashboardResponse(
        total_workers=worker_stats["total_workers"],
        online=worker_stats["online"],
        offline=worker_stats["offline"],
        idle=worker_stats["idle"],
        busy=worker_stats["busy"],
        average_cpu=worker_stats["average_cpu"],
        average_ram=worker_stats["average_ram"],
        running_jobs=running_jobs,
    )
