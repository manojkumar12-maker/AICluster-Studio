import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....models.studio import StudioLayout

logger = logging.getLogger(__name__)
router = APIRouter(tags=["layout"])


@router.get("/layout")
async def get_layout(workspace_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StudioLayout).where(StudioLayout.workspace_id == workspace_id, StudioLayout.active == True)
    )
    layout = result.scalar_one_or_none()
    if not layout:
        return {"panels": {"explorer": True, "editor": True, "terminal": False, "chat": False, "workflow": False, "plugin_center": False}}
    return {"id": layout.id, "name": layout.name, "panels": layout.panels}


@router.post("/layout")
async def save_layout(data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StudioLayout).where(StudioLayout.workspace_id == data["workspace_id"], StudioLayout.active == True)
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.panels = data.get("panels", existing.panels)
        existing.name = data.get("name", existing.name)
    else:
        layout = StudioLayout(workspace_id=data["workspace_id"], name=data.get("name", "default"),
                               panels=data.get("panels", {}))
        db.add(layout)
    await db.commit()
    return {"status": "saved"}
