import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.repository import Repository, Symbol, RepositoryFile

logger = logging.getLogger(__name__)

MAX_CONTEXT_SYMBOLS = 20
MAX_CONTEXT_FILES = 5


class ContextBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_context(self, repository_id: str, query: str) -> str:
        parts = []

        repo = await self.db.get(Repository, repository_id)
        if repo:
            parts.append(f"Repository: {repo.name} ({repo.language or 'unknown'})")
            parts.append(f"Files: {repo.total_files} | Symbols: {repo.total_symbols}")

        query_words = [w.lower() for w in query.split() if len(w) > 2]
        if query_words:
            conditions = [Symbol.name.ilike(f"%{w}%") for w in query_words[:3]]
            result = await self.db.execute(
                select(Symbol).where(Symbol.repository_id == repository_id)
                .where(conditions[0] if conditions else True)
                .limit(MAX_CONTEXT_SYMBOLS)
            )
            symbols = list(result.scalars().all())
            if symbols:
                parts.append("\n### Relevant Symbols")
                for s in symbols[:10]:
                    parts.append(f"- {s.symbol_type} `{s.name}` ({s.language}, line {s.line_start})")

        result = await self.db.execute(
            select(RepositoryFile).where(RepositoryFile.repository_id == repository_id)
            .order_by(RepositoryFile.complexity.desc().nullslast())
            .limit(MAX_CONTEXT_FILES)
        )
        files = list(result.scalars().all())
        if files:
            parts.append("\n### Key Files")
            for f in files:
                parts.append(f"- `{f.path}` ({f.language}, {f.lines} lines)")

        return "\n".join(parts)
