from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...database import get_db
from ...models.repository import (
    Repository, RepositoryFile, Symbol, SymbolImport, SymbolReference,
    DependencyEdge, CodeMetric, KnowledgeNode, KnowledgeEdge,
)
from ...repository.indexer.service import RepositoryIndexer
from ...repository.search.service import SearchService
from ...repository.metrics.service import CodeMetricsService
from ...websocket.manager import ws_manager

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("")
async def create_repository(data: dict, db: AsyncSession = Depends(get_db)):
    repo = Repository(name=data["name"], path=data["path"])
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    await ws_manager.broadcast("repository_added", {"id": repo.id, "name": repo.name})
    return {"id": repo.id, "name": repo.name, "path": repo.path, "status": repo.status}


@router.get("")
async def list_repositories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).order_by(Repository.created_at.desc()))
    repos = result.scalars().all()
    return [{"id": r.id, "name": r.name, "path": r.path, "status": r.status,
             "language": r.language, "total_files": r.total_files, "total_symbols": r.total_symbols,
             "last_scanned_at": r.last_scanned_at.isoformat() if r.last_scanned_at else None,
             "created_at": r.created_at.isoformat()} for r in repos]


@router.get("/{repo_id}")
async def get_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(404, "Repository not found")
    return {"id": repo.id, "name": repo.name, "path": repo.path, "status": repo.status,
            "language": repo.language, "total_files": repo.total_files, "total_lines": repo.total_lines,
            "total_symbols": repo.total_symbols, "last_scanned_at": repo.last_scanned_at.isoformat() if repo.last_scanned_at else None,
            "created_at": repo.created_at.isoformat()}


@router.delete("/{repo_id}")
async def delete_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(404, "Repository not found")
    await db.delete(repo)
    await db.commit()
    return {"status": "deleted"}


@router.post("/{repo_id}/scan")
async def scan_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(404, "Repository not found")
    indexer = RepositoryIndexer(db)
    result = await indexer.scan_and_index(repo_id, repo.path)
    await ws_manager.broadcast("scan_complete", {"id": repo_id, "files": result.get("files", 0)})
    return result


@router.post("/{repo_id}/rescan")
async def rescan_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(404, "Repository not found")
    await db.execute(RepositoryFile.__table__.delete().where(RepositoryFile.repository_id == repo_id))
    await db.execute(Symbol.__table__.delete().where(Symbol.repository_id == repo_id))
    await db.execute(SymbolImport.__table__.delete().where(SymbolImport.repository_id == repo_id))
    await db.commit()
    indexer = RepositoryIndexer(db)
    result = await indexer.scan_and_index(repo_id, repo.path)
    return result


@router.get("/{repo_id}/symbols")
async def get_symbols(repo_id: str, type: Optional[str] = None, limit: int = 500, db: AsyncSession = Depends(get_db)):
    q = select(Symbol).where(Symbol.repository_id == repo_id)
    if type:
        q = q.where(Symbol.symbol_type == type)
    q = q.limit(limit)
    result = await db.execute(q)
    symbols = result.scalars().all()
    return [{"id": s.id, "name": s.name, "type": s.symbol_type, "language": s.language,
             "line": s.line_start, "signature": s.signature, "visibility": s.visibility,
             "complexity": s.complexity, "docstring": s.docstring[:100] if s.docstring else None} for s in symbols]


@router.get("/{repo_id}/dependencies")
async def get_dependencies(repo_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DependencyEdge).where(DependencyEdge.repository_id == repo_id).limit(500)
    )
    deps = result.scalars().all()
    return [{"source_file": d.source_file_id, "target_file": d.target_file_id, "type": d.dependency_type} for d in deps]


@router.get("/{repo_id}/metrics")
async def get_metrics(repo_id: str, db: AsyncSession = Depends(get_db)):
    metrics = CodeMetricsService(db)
    return await metrics.compute_metrics(repo_id)


@router.get("/{repo_id}/health")
async def get_health(repo_id: str, db: AsyncSession = Depends(get_db)):
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(404, "Repository not found")
    metrics = CodeMetricsService(db)
    m = await metrics.compute_metrics(repo_id)
    large_files = await db.execute(
        select(RepositoryFile.path, RepositoryFile.lines)
        .where(RepositoryFile.repository_id == repo_id, RepositoryFile.lines > 500)
        .order_by(RepositoryFile.lines.desc()).limit(10)
    )
    high_complexity = await db.execute(
        select(RepositoryFile.path, RepositoryFile.complexity)
        .where(RepositoryFile.repository_id == repo_id, RepositoryFile.complexity > 10)
        .order_by(RepositoryFile.complexity.desc()).limit(10)
    )
    return {
        "status": "healthy" if m.get("total_files", 0) > 0 else "empty",
        "total_files": m.get("total_files", 0), "total_lines": m.get("total_lines", 0),
        "avg_complexity": m.get("avg_complexity", 0),
        "large_files": [{"path": r.path, "lines": r.lines} for r in large_files],
        "high_complexity_files": [{"path": r.path, "complexity": r.complexity} for r in high_complexity],
    }


@router.get("/{repo_id}/files")
async def get_files(repo_id: str, folder: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    q = select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
    if folder:
        q = q.where(RepositoryFile.path.like(f"{folder}%"))
    q = q.order_by(RepositoryFile.path).limit(500)
    result = await db.execute(q)
    files = result.scalars().all()
    return [{"id": f.id, "path": f.path, "language": f.language, "lines": f.lines,
             "code_lines": f.code_lines, "complexity": f.complexity} for f in files]


@router.get("/{repo_id}/file/{file_id}/metrics")
async def get_file_metrics(repo_id: str, file_id: str, db: AsyncSession = Depends(get_db)):
    metrics = CodeMetricsService(db)
    return await metrics.compute_file_metrics(repo_id, file_id)


@router.get("/{repo_id}/knowledge")
async def get_knowledge_graph(repo_id: str, db: AsyncSession = Depends(get_db)):
    nodes = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.repository_id == repo_id).limit(500)
    )
    edges = await db.execute(
        select(KnowledgeEdge).where(KnowledgeEdge.repository_id == repo_id).limit(1000)
    )
    return {
        "nodes": [{"id": n.id, "type": n.node_type, "name": n.name, "data": n.data} for n in nodes.scalars()],
        "edges": [{"source": e.source_node_id, "target": e.target_node_id, "type": e.edge_type} for e in edges.scalars()],
    }


@router.get("/search")
async def search(q: str = Query(...), repo_id: Optional[str] = None,
                  type: Optional[str] = Query(None, alias="search_type"),
                  language: Optional[str] = None, mode: str = "symbol",
                  regex: bool = False, limit: int = 50, db: AsyncSession = Depends(get_db)):
    search_svc = SearchService(db)
    if mode == "symbol":
        results = await search_svc.search_symbols(q, repo_id, type, language, limit)
    elif mode == "file":
        results = await search_svc.search_files(q, repo_id, language, limit)
    elif mode == "text":
        results = await search_svc.search_text(q, repo_id, language, regex, limit)
    elif mode == "reference":
        results = await search_svc.search_references(q, repo_id, limit)
    else:
        results = []
    return {"query": q, "mode": mode, "results": results, "count": len(results)}
