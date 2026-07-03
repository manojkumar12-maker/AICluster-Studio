from fastapi import APIRouter
from .workspaces import router as workspaces_router
from .projects import router as projects_router
from .layout import router as layout_router

router = APIRouter(prefix="/studio", tags=["studio"])
router.include_router(workspaces_router)
router.include_router(projects_router)
router.include_router(layout_router)
