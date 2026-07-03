import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.workflow import CacheEntry

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self, db: AsyncSession, ttl_seconds: int = 3600):
        self.db = db
        self.ttl_seconds = ttl_seconds

    def make_key(self, workflow_type: str, task_type: str, payload: dict) -> str:
        raw = f"{workflow_type}:{task_type}:{json.dumps(payload, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get(self, cache_key: str) -> dict | None:
        result = await self.db.execute(
            select(CacheEntry).where(CacheEntry.cache_key == cache_key)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return None
        if entry.expires_at and entry.expires_at < datetime.now(timezone.utc):
            await self.db.delete(entry)
            await self.db.commit()
            return None
        logger.info(f"Cache hit: {cache_key[:16]}...")
        return entry.result

    async def set(self, cache_key: str, workflow_type: str, task_type: str,
                  input_hash: str, result: dict) -> CacheEntry:
        entry = CacheEntry(
            cache_key=cache_key, workflow_type=workflow_type,
            task_type=task_type, input_hash=input_hash, result=result,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds),
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry
