import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.ai import AISession, AIMessage

logger = logging.getLogger(__name__)


class ConversationManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_message(self, session_id: str, role: str, content: str,
                          model_id: str | None = None, tokens: int | None = None,
                          tool_calls: list | None = None) -> AIMessage:
        msg = AIMessage(
            session_id=session_id, role=role, content=content,
            model_id=model_id, tokens=tokens, tool_calls=tool_calls or [],
        )
        self.db.add(msg)
        session = await self.db.get(AISession, session_id)
        if session:
            session.total_messages += 1
            if tokens:
                session.total_tokens += tokens
            session.last_active_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_history(self, session_id: str, limit: int = 50) -> list[AIMessage]:
        result = await self.db.execute(
            select(AIMessage).where(AIMessage.session_id == session_id)
            .order_by(AIMessage.created_at).limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(self, session_id: str, last_n: int = 10) -> list[dict]:
        result = await self.db.execute(
            select(AIMessage).where(AIMessage.session_id == session_id)
            .order_by(AIMessage.created_at.desc()).limit(last_n)
        )
        msgs = list(result.scalars().all())
        msgs.reverse()
        return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat(),
                 "tokens": m.tokens} for m in msgs]
