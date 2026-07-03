import hashlib
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.repository import Repository, RepositoryFile, Symbol, SymbolImport, SymbolReference, DependencyEdge, CodeMetric, RepositoryEvent
from ..scanner.service import FileScanner
from ..parser.service import SymbolParser

logger = logging.getLogger(__name__)


class RepositoryIndexer:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.parser = SymbolParser()

    async def scan_and_index(self, repo_id: str, path: str) -> dict:
        repo = await self.db.get(Repository, repo_id)
        if not repo:
            return {"error": "Repository not found"}

        repo.status = "scanning"
        await self.db.commit()

        scanner = FileScanner(path)
        files_count = 0
        symbols_count = 0
        total_lines = 0

        async for file_data in scanner.scan():
            result = await self.db.execute(
                select(RepositoryFile).where(
                    RepositoryFile.repository_id == repo_id,
                    RepositoryFile.path == file_data["path"],
                )
            )
            existing = result.scalar_one_or_none()

            if existing and existing.hash == file_data["hash"]:
                continue

            if existing:
                for attr, value in file_data.items():
                    if hasattr(existing, attr) and attr not in ("id", "repository_id", "path"):
                        setattr(existing, attr, value)
                rf = existing
            else:
                rf = RepositoryFile(repository_id=repo_id, **{k: v for k, v in file_data.items() if hasattr(RepositoryFile, k)})
                self.db.add(rf)

            await self.db.flush()
            await self.db.refresh(rf)

            if not file_data.get("is_binary") and file_data.get("language"):
                try:
                    content = ""
                    with open(f"{path}/{file_data['path']}", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    symbols_data = self.parser.parse(file_data["path"], content, file_data["language"])
                    for sym in symbols_data:
                        if sym.get("symbol_type") == "_imports":
                            for imp in sym.get("imports", []):
                                si = SymbolImport(
                                    repository_id=repo_id, file_id=rf.id,
                                    source=imp["source"], imported_name=imp.get("imported_name", ""),
                                    is_relative=imp.get("is_relative", False), line=imp.get("line", 0),
                                )
                                self.db.add(si)
                            continue
                        symbol = Symbol(
                            repository_id=repo_id, file_id=rf.id,
                            name=sym.get("name", ""), symbol_type=sym.get("symbol_type", "unknown"),
                            language=file_data["language"],
                            line_start=sym.get("line_start", 0), line_end=sym.get("line_end", 0),
                            column_start=sym.get("column_start", 0), column_end=sym.get("column_end", 0),
                            signature=sym.get("signature"), docstring=sym.get("docstring"),
                            parameters=sym.get("parameters", []), decorators=sym.get("decorators", []),
                            visibility=sym.get("visibility", "public"),
                            complexity=sym.get("complexity"),
                        )
                        self.db.add(symbol)
                        symbols_count += 1
                except Exception as e:
                    logger.warning(f"Failed to parse {file_data['path']}: {e}")

            files_count += 1
            total_lines += file_data.get("lines", 0)

        repo.total_files = files_count
        repo.total_lines = total_lines
        repo.total_symbols = symbols_count
        repo.status = "scanned"
        repo.last_scanned_at = datetime.now(timezone.utc)
        await self.db.commit()

        event = RepositoryEvent(repository_id=repo_id, event_type="scan_complete", data={"files": files_count, "symbols": symbols_count})
        self.db.add(event)
        await self.db.commit()

        logger.info(f"Indexed {repo.name}: {files_count} files, {symbols_count} symbols")
        return {"files": files_count, "symbols": symbols_count}

    async def get_file_hash(self, filepath: str) -> str:
        h = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
        except Exception:
            return ""
        return h.hexdigest()
