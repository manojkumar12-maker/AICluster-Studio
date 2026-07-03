from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.log import SystemLog


class LogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, level: str, message: str, source: str | None = None):
        entry = SystemLog(
            level=level.upper(),
            message=message,
            source=source,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(entry)
        await self.db.commit()

    async def info(self, message: str, source: str | None = None):
        await self.log("INFO", message, source)

    async def warning(self, message: str, source: str | None = None):
        await self.log("WARNING", message, source)

    async def error(self, message: str, source: str | None = None):
        await self.log("ERROR", message, source)

    async def get_all(
        self, level: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[SystemLog]:
        query = select(SystemLog).order_by(SystemLog.created_at.desc())
        if level:
            query = query.where(SystemLog.level == level.upper())
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, level: str | None = None) -> int:
        query = select(func.count(SystemLog.id))
        if level:
            query = query.where(SystemLog.level == level.upper())
        return await self.db.scalar(query) or 0
