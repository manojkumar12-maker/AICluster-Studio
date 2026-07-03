import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.ai import AISession, AIMessage

logger = logging.getLogger(__name__)

SESSION_TIMEOUT_HOURS = 24


class SessionManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str | None = None, model_id: str | None = None,
                     repository_id: str | None = None) -> AISession:
        session = AISession(
            user_id=user_id, model_id=model_id, repository_id=repository_id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=SESSION_TIMEOUT_HOURS),
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        logger.info(f"Session created: {session.id}")
        return session

    async def get(self, session_id: str) -> AISession | None:
        session = await self.db.get(AISession, session_id)
        if session and session.expires_at and session.expires_at < datetime.now(timezone.utc):
            session.status = "expired"
            await self.db.commit()
            return None
        return session

    async def delete(self, session_id: str) -> bool:
        session = await self.db.get(AISession, session_id)
        if not session:
            return False
        session.status = "deleted"
        await self.db.commit()
        return True

    async def list_active(self, limit: int = 50) -> list[AISession]:
        result = await self.db.execute(
            select(AISession).where(AISession.status == "active")
            .order_by(AISession.last_active_at.desc()).limit(limit)
        )
        sessions = result.scalars().all()
        now = datetime.now(timezone.utc)
        active = []
        for s in sessions:
            if s.expires_at and s.expires_at < now:
                s.status = "expired"
            else:
                active.append(s)
        await self.db.commit()
        return active

    async def touch(self, session_id: str):
        session = await self.db.get(AISession, session_id)
        if session:
            session.last_active_at = datetime.now(timezone.utc)
            await self.db.commit()
