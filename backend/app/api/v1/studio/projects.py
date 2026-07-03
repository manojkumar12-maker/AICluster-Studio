import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....models.studio import StudioProject, StudioBookmark

logger = logging.getLogger(__name__)
router = APIRouter(tags=["projects"])


@router.get("/projects")
async def list_projects(workspace_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StudioProject).where(StudioProject.workspace_id == workspace_id)
        .order_by(StudioProject.pinned.desc(), StudioProject.last_opened_at.desc())
    )
    projects = result.scalars().all()
    return [{"id": p.id, "name": p.name, "type": p.type, "repository_id": p.repository_id,
             "pinned": p.pinned, "created_at": p.created_at.isoformat()} for p in projects]


@router.post("/projects")
async def create_project(data: dict, db: AsyncSession = Depends(get_db)):
    proj = StudioProject(
        workspace_id=data["workspace_id"], name=data["name"],
        repository_id=data.get("repository_id"), path=data.get("path"),
        type=data.get("type", "general"), tags=data.get("tags", []),
    )
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return {"id": proj.id, "name": proj.name}


@router.delete("/projects/{proj_id}")
async def delete_project(proj_id: str, db: AsyncSession = Depends(get_db)):
    proj = await db.get(StudioProject, proj_id)
    if not proj:
        raise HTTPException(404, "Project not found")
    await db.delete(proj)
    await db.commit()
    return {"status": "deleted"}


@router.post("/bookmarks")
async def add_bookmark(data: dict, db: AsyncSession = Depends(get_db)):
    bm = StudioBookmark(workspace_id=data["workspace_id"], type=data["type"],
                         label=data["label"], target=data["target"])
    db.add(bm)
    await db.commit()
    return {"id": bm.id, "label": bm.label}


@router.get("/bookmarks")
async def get_bookmarks(workspace_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StudioBookmark).where(StudioBookmark.workspace_id == workspace_id).order_by(StudioBookmark.created_at)
    )
    return [{"id": b.id, "type": b.type, "label": b.label, "target": b.target} for b in result.scalars()]
