import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.repository import Symbol, RepositoryFile

logger = logging.getLogger(__name__)


class ContextOptimizer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def rank_context(self, repository_id: str, query: str, max_tokens: int = 3000) -> str:
        query_words = [w.lower() for w in query.split() if len(w) > 2]
        parts = []
        token_budget = max_tokens
        used_tokens = 0

        if query_words:
            result = await self.db.execute(
                select(Symbol).where(Symbol.repository_id == repository_id).limit(30)
            )
            symbols = list(result.scalars().all())
            ranked = sorted(symbols, key=lambda s: self._relevance(s.name, query_words), reverse=True)
            for symbol in ranked[:15]:
                entry = f"- {symbol.symbol_type} `{symbol.name}` ({symbol.language}, line {symbol.line_start})"
                tokens = len(entry) // 4 + 1
                if used_tokens + tokens > token_budget:
                    break
                parts.append(entry)
                used_tokens += tokens

        result = await self.db.execute(
            select(RepositoryFile).where(RepositoryFile.repository_id == repository_id)
            .order_by(RepositoryFile.complexity.desc().nullslast()).limit(10)
        )
        files = list(result.scalars().all())
        for f in files:
            entry = f"- `{f.path}` ({f.language}, {f.lines} lines)"
            tokens = len(entry) // 4 + 1
            if used_tokens + tokens > token_budget:
                break
            parts.append(entry)
            used_tokens += tokens

        result = "\n".join(parts)
        compressed = self.compress(result, max_tokens)
        return compressed

    def compress(self, text: str, max_tokens: int) -> str:
        estimated = len(text) // 4 + 1
        if estimated <= max_tokens:
            return text
        ratio = max_tokens / estimated
        max_chars = int(len(text) * ratio * 0.8)
        return text[:max_chars] + "\n... (truncated)"

    def _relevance(self, name: str, query_words: list[str]) -> float:
        name_lower = name.lower()
        score = 0.0
        for word in query_words:
            if word in name_lower:
                score += 2.0
            if name_lower.startswith(word) or name_lower.endswith(word):
                score += 1.0
        return score

    def sliding_window(self, content: str, max_tokens: int = 2048, overlap_tokens: int = 256) -> list[str]:
        estimated_total = len(content) // 4 + 1
        if estimated_total <= max_tokens:
            return [content]
        chunk_size = max_tokens * 4
        overlap_size = overlap_tokens * 4
        chunks = []
        start = 0
        while start < len(content):
            end = start + chunk_size
            chunks.append(content[start:end])
            start += chunk_size - overlap_size
        return chunks
