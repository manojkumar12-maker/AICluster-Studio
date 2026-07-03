import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....models.studio import StudioWorkspace, StudioPreference, StudioHistory

logger = logging.getLogger(__name__)
router = APIRouter(tags=["workspaces"])


@router.get("/workspaces")
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StudioWorkspace).order_by(StudioWorkspace.created_at.desc()))
    workspaces = result.scalars().all()
    return [{"id": w.id, "name": w.name, "description": w.description,
             "project_count": len(w.projects or []), "created_at": w.created_at.isoformat()} for w in workspaces]


@router.post("/workspaces")
async def create_workspace(data: dict, db: AsyncSession = Depends(get_db)):
    ws = StudioWorkspace(name=data["name"], description=data.get("description"),
                          layout={"panels": {"explorer": True, "editor": True, "terminal": False, "chat": False}})
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    return {"id": ws.id, "name": ws.name}


@router.get("/workspaces/{ws_id}")
async def get_workspace(ws_id: str, db: AsyncSession = Depends(get_db)):
    ws = await db.get(StudioWorkspace, ws_id)
    if not ws:
        raise HTTPException(404, "Workspace not found")
    return {"id": ws.id, "name": ws.name, "description": ws.description,
            "layout": ws.layout, "settings": ws.settings, "projects": ws.projects}


@router.delete("/workspaces/{ws_id}")
async def delete_workspace(ws_id: str, db: AsyncSession = Depends(get_db)):
    ws = await db.get(StudioWorkspace, ws_id)
    if not ws:
        raise HTTPException(404, "Workspace not found")
    await db.delete(ws)
    await db.commit()
    return {"status": "deleted"}


@router.get("/history")
async def get_history(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StudioHistory).order_by(StudioHistory.created_at.desc()).limit(limit))
    return [{"id": h.id, "action": h.action, "target": h.target, "created_at": h.created_at.isoformat()} for h in result.scalars()]


@router.post("/preferences")
async def set_preference(data: dict, db: AsyncSession = Depends(get_db)):
    pref = StudioPreference(workspace_id=data["workspace_id"], key=data["key"], value=data["value"])
    db.add(pref)
    await db.commit()
    return {"status": "saved"}


@router.get("/preferences/{ws_id}")
async def get_preferences(ws_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StudioPreference).where(StudioPreference.workspace_id == ws_id))
    prefs = result.scalars().all()
    return {p.key: p.value for p in prefs}
