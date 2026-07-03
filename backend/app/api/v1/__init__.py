from fastapi import APIRouter
from .workers import router as workers_router
from .jobs import router as jobs_router
from .dashboard import router as dashboard_router
from .health import router as health_router
from .auth import router as auth_router
from .logs import router as logs_router
from .workflows import router as workflows_router
from .repositories import router as repositories_router
from .ai import router as ai_router
from .agents import router as agents_router
from .engineering import router as engineering_router
from .production import router as production_router
from .plugins import router as plugins_router
from .studio import router as studio_router

from ...audit.api import router as audit_router

router = APIRouter(prefix="/api/v1")
router.include_router(workers_router)
router.include_router(jobs_router)
router.include_router(dashboard_router)
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(logs_router)
router.include_router(workflows_router)
router.include_router(repositories_router)
router.include_router(ai_router)
router.include_router(agents_router)
router.include_router(engineering_router)
router.include_router(production_router)
router.include_router(plugins_router)
router.include_router(studio_router)
router.include_router(audit_router)
