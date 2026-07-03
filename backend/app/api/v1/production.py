import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...production.monitoring.service import MonitoringService
from ...production.health.service import HealthService
from ...production.diagnostics.service import DiagnosticsService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/production", tags=["production"])


@router.get("/monitoring")
async def get_monitoring(db: AsyncSession = Depends(get_db)):
    monitor = MonitoringService(db)
    return await monitor.get_all_metrics()


@router.get("/monitoring/system")
async def get_system_metrics(db: AsyncSession = Depends(get_db)):
    monitor = MonitoringService(db)
    return await monitor.get_system_metrics()


@router.get("/monitoring/cluster")
async def get_cluster_metrics(db: AsyncSession = Depends(get_db)):
    monitor = MonitoringService(db)
    return await monitor.get_cluster_metrics()


@router.get("/health")
async def get_health():
    health = HealthService()
    return await health.check_all()


@router.get("/health/{subsystem}")
async def get_subsystem_health(subsystem: str):
    health = HealthService()
    result = await health.check_subsystem(subsystem)
    if not result.get("healthy"):
        raise HTTPException(503, detail=result.get("error", "Unhealthy"))
    return result


@router.get("/diagnostics")
async def get_diagnostics():
    diag = DiagnosticsService()
    return {"results": await diag.run_all()}


@router.get("/diagnostics/{check}")
async def get_diagnostic_check(check: str):
    diag = DiagnosticsService()
    return await diag.run_check(check)
