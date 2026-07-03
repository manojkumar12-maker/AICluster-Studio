import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.agent import AgentMessage

logger = logging.getLogger(__name__)

MESSAGE_TYPES = [
    "task_request", "task_result", "question", "review",
    "approval", "artifact", "error", "status", "heartbeat",
]


class CommunicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send(self, sender_id: str, recipient_id: str, message_type: str,
                   content: str, context: dict | None = None,
                   task_id: str | None = None, requires_response: bool = False) -> AgentMessage:
        msg = AgentMessage(
            sender=sender_id, recipient=recipient_id,
            message_type=message_type, content=content,
            context=context or {}, task_id=task_id,
            requires_response=requires_response,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_inbox(self, agent_id: str, limit: int = 50) -> list[AgentMessage]:
        result = await self.db.execute(
            select(AgentMessage).where(AgentMessage.recipient == agent_id)
            .order_by(AgentMessage.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_unread(self, agent_id: str) -> list[AgentMessage]:
        result = await self.db.execute(
            select(AgentMessage).where(AgentMessage.recipient == agent_id, AgentMessage.read == False)
            .order_by(AgentMessage.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_read(self, message_id: str):
        msg = await self.db.get(AgentMessage, message_id)
        if msg:
            msg.read = True
            await self.db.commit()

    async def get_conversation(self, agent_a: str, agent_b: str, limit: int = 100) -> list[AgentMessage]:
        result = await self.db.execute(
            select(AgentMessage).where(
                ((AgentMessage.sender == agent_a) & (AgentMessage.recipient == agent_b)) |
                ((AgentMessage.sender == agent_b) & (AgentMessage.recipient == agent_a))
            ).order_by(AgentMessage.created_at).limit(limit)
        )
        return list(result.scalars().all())

    async def get_workflow_messages(self, workflow_id: str) -> list[AgentMessage]:
        result = await self.db.execute(
            select(AgentMessage).where(AgentMessage.workflow_id == workflow_id)
            .order_by(AgentMessage.created_at)
        )
        return list(result.scalars().all())
