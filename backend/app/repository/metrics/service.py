import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.repository import Repository, RepositoryFile, Symbol, CodeMetric

logger = logging.getLogger(__name__)


class CodeMetricsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_metrics(self, repo_id: str) -> dict:
        result = await self.db.execute(
            select(func.count(RepositoryFile.id), func.sum(RepositoryFile.lines),
                   func.sum(RepositoryFile.code_lines), func.avg(RepositoryFile.complexity))
            .where(RepositoryFile.repository_id == repo_id)
        )
        row = result.one()
        total_files = row[0] or 0
        total_lines = row[1] or 0
        total_code = row[2] or 0
        avg_complexity = float(row[3] or 0)

        result = await self.db.execute(
            select(func.count(Symbol.id)).where(Symbol.repository_id == repo_id)
        )
        total_symbols = result.scalar() or 0

        result = await self.db.execute(
            select(func.count(Symbol.id), Symbol.symbol_type)
            .where(Symbol.repository_id == repo_id)
            .group_by(Symbol.symbol_type)
        )
        symbol_counts = {row.symbol_type: row[0] for row in result}

        result = await self.db.execute(
            select(RepositoryFile.language, func.count(RepositoryFile.id), func.sum(RepositoryFile.lines))
            .where(RepositoryFile.repository_id == repo_id)
            .group_by(RepositoryFile.language)
        )
        language_dist = {row.language: {"files": row[1], "lines": row[2] or 0} for row in result}

        result = await self.db.execute(
            select(RepositoryFile.path, RepositoryFile.complexity)
            .where(RepositoryFile.repository_id == repo_id, RepositoryFile.complexity.isnot(None))
            .order_by(RepositoryFile.complexity.desc())
            .limit(10)
        )
        complex_files = [{"path": row.path, "complexity": row.complexity} for row in result]

        metrics = {
            "total_files": total_files, "total_lines": total_lines, "total_code_lines": total_code,
            "total_symbols": total_symbols, "avg_complexity": round(avg_complexity, 2),
            "symbols_by_type": symbol_counts, "language_distribution": language_dist,
            "most_complex_files": complex_files,
        }

        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                cm = CodeMetric(repository_id=repo_id, metric_type=key, value=float(value))
                self.db.add(cm)
        await self.db.commit()

        return metrics

    async def compute_file_metrics(self, repo_id: str, file_id: str) -> dict:
        result = await self.db.execute(
            select(RepositoryFile).where(RepositoryFile.id == file_id, RepositoryFile.repository_id == repo_id)
        )
        f = result.scalar_one_or_none()
        if not f:
            return {}
        result = await self.db.execute(
            select(func.count(Symbol.id)).where(Symbol.file_id == file_id)
        )
        symbol_count = result.scalar() or 0
        result = await self.db.execute(
            select(func.avg(Symbol.complexity)).where(Symbol.file_id == file_id)
        )
        avg_sym_complexity = float(result.scalar() or 0)
        main_index = max(0, min(100, 100 - (f.complexity or 0) * 2 - (f.lines / 100) * 5))
        return {
            "file_id": file_id, "path": f.path, "lines": f.lines, "code_lines": f.code_lines,
            "symbol_count": symbol_count, "complexity": f.complexity,
            "avg_symbol_complexity": round(avg_sym_complexity, 2),
            "maintainability_index": round(main_index, 1),
            "comment_ratio": round(f.comment_lines / max(f.lines, 1) * 100, 1),
        }
