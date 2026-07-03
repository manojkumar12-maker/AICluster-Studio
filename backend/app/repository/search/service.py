import re
import logging
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.repository import Repository, RepositoryFile, Symbol

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_symbols(self, query: str, repo_id: str | None = None,
                              symbol_type: str | None = None, language: str | None = None,
                              limit: int = 50) -> list[dict]:
        q = select(Symbol)
        conditions = [Symbol.name.ilike(f"%{query}%")]
        if repo_id:
            conditions.append(Symbol.repository_id == repo_id)
        if symbol_type:
            conditions.append(Symbol.symbol_type == symbol_type)
        if language:
            conditions.append(Symbol.language == language)
        q = q.where(or_(*conditions)).limit(limit)
        result = await self.db.execute(q)
        symbols = result.scalars().all()
        return [{"id": s.id, "name": s.name, "type": s.symbol_type, "language": s.language,
                 "file_id": s.file_id, "line": s.line_start, "signature": s.signature} for s in symbols]

    async def search_files(self, query: str, repo_id: str | None = None,
                            language: str | None = None, limit: int = 50) -> list[dict]:
        q = select(RepositoryFile)
        conditions = [RepositoryFile.path.ilike(f"%{query}%")]
        if repo_id:
            conditions.append(RepositoryFile.repository_id == repo_id)
        if language:
            conditions.append(RepositoryFile.language == language)
        q = q.where(or_(*conditions)).limit(limit)
        result = await self.db.execute(q)
        files = result.scalars().all()
        return [{"id": f.id, "path": f.path, "language": f.language, "lines": f.lines,
                 "code_lines": f.code_lines, "complexity": f.complexity} for f in files]

    async def search_text(self, query: str, repo_id: str | None = None,
                           language: str | None = None, regex: bool = False,
                           limit: int = 50) -> list[dict]:
        results = []
        from ...models.repository import Repository
        if repo_id:
            repo_result = await self.db.execute(select(Repository).where(Repository.id == repo_id))
            repo = repo_result.scalar_one_or_none()
            if not repo:
                return []
            repos = [repo]
        else:
            repo_result = await self.db.execute(select(Repository))
            repos = list(repo_result.scalars().all())

        pattern = re.compile(query, re.IGNORECASE) if regex else None

        for repo in repos:
            files_result = await self.db.execute(
                select(RepositoryFile).where(RepositoryFile.repository_id == repo.id)
                .where(RepositoryFile.is_binary == False)
                .limit(100)
            )
            files = list(files_result.scalars().all())

            import os
            for rf in files[:limit]:
                try:
                    fpath = os.path.join(repo.path, rf.path)
                    with open(fpath, encoding="utf-8", errors="replace") as f:
                        for i, line in enumerate(f, 1):
                            if regex and pattern:
                                if pattern.search(line):
                                    results.append({"file_id": rf.id, "path": rf.path, "line": i, "content": line.strip(), "language": rf.language})
                            elif query.lower() in line.lower():
                                results.append({"file_id": rf.id, "path": rf.path, "line": i, "content": line.strip(), "language": rf.language})
                            if len(results) >= limit:
                                break
                except Exception:
                    continue
                if len(results) >= limit:
                    break
        return results[:limit]

    async def search_references(self, symbol_name: str, repo_id: str | None = None, limit: int = 50) -> list[dict]:
        q = select(SymbolReference)
        conditions = [SymbolReference.id.isnot(None)]
        result = await self.db.execute(
            select(Symbol).where(Symbol.name == symbol_name)
        )
        symbols = result.scalars().all()
        if not symbols:
            return []
        symbol_ids = [s.id for s in symbols]
        refs_result = await self.db.execute(
            select(SymbolReference).where(SymbolReference.source_symbol_id.in_(symbol_ids)).limit(limit)
        )
        refs = refs_result.scalars().all()
        return [{"source": r.source_symbol_id, "target": r.target_symbol_id,
                 "type": r.reference_type, "line": r.line} for r in refs]
