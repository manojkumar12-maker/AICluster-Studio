import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.agent import Agent, AgentTask, AgentMessage, AgentReview, AgentMerge, AgentMetric
from ...agents.registry.service import AgentRegistry
from ...agents.orchestrator.service import Orchestrator
from ...agents.communication.service import CommunicationService
from ...agents.review.service import ReviewService
from ...agents.merge.service import MergeService
from ...websocket.manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/run")
async def run_agents(data: dict, db: AsyncSession = Depends(get_db)):
    orchestrator = Orchestrator(db)
    result = await orchestrator.run(
        request=data.get("request", ""),
        request_type=data.get("type", "default"),
        workflow_id=data.get("workflow_id"),
    )
    return result


@router.post("/run/sync")
async def run_agents_sync(data: dict, db: AsyncSession = Depends(get_db)):
    orchestrator = Orchestrator(db)
    result = await orchestrator.run_sync(
        request=data.get("request", ""),
        request_type=data.get("type", "default"),
        workflow_id=data.get("workflow_id"),
    )
    return result


@router.get("")
async def list_agents(db: AsyncSession = Depends(get_db)):
    registry = AgentRegistry(db)
    agents = await registry.list_all()
    return [{"id": a.id, "name": a.name, "role": a.role, "status": a.status,
             "capabilities": a.capabilities, "priority": a.priority} for a in agents]


@router.get("/{agent_id}")
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    registry = AgentRegistry(db)
    agent = await registry.get(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    return {"id": agent.id, "name": agent.name, "role": agent.role, "status": agent.status,
            "description": agent.description, "capabilities": agent.capabilities,
            "permissions": agent.permissions, "allowed_tools": agent.allowed_tools,
            "model_preference": agent.model_preference, "priority": agent.priority}


@router.post("/register")
async def register_agent(data: dict, db: AsyncSession = Depends(get_db)):
    registry = AgentRegistry(db)
    agent = await registry.register(
        name=data["name"], role=data.get("role", "engineer"),
        description=data.get("description"), capabilities=data.get("capabilities"),
        permissions=data.get("permissions"), allowed_tools=data.get("allowed_tools"),
        model_preference=data.get("model_preference"), priority=data.get("priority", 0),
    )
    await ws_manager.broadcast("agent_registered", {"id": agent.id, "name": agent.name})
    return {"id": agent.id, "name": agent.name, "role": agent.role, "status": agent.status}


@router.post("/seed")
async def seed_default_agents(db: AsyncSession = Depends(get_db)):
    registry = AgentRegistry(db)
    await registry.seed_default_agents()
    agents = await registry.list_all()
    return {"status": "seeded", "count": len(agents)}


@router.post("/{agent_id}/pause")
async def pause_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    registry = AgentRegistry(db)
    await registry.set_status(agent_id, "paused")
    return {"status": "paused"}


@router.post("/{agent_id}/resume")
async def resume_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    registry = AgentRegistry(db)
    await registry.set_status(agent_id, "idle")
    return {"status": "resumed"}


@router.post("/{agent_id}/disable")
async def disable_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    registry = AgentRegistry(db)
    await registry.set_status(agent_id, "disabled")
    return {"status": "disabled"}


@router.get("/messages")
async def get_messages(agent_id: str | None = None, unread: bool = False,
                       db: AsyncSession = Depends(get_db)):
    comms = CommunicationService(db)
    if agent_id and unread:
        msgs = await comms.get_unread(agent_id)
    elif agent_id:
        msgs = await comms.get_inbox(agent_id)
    else:
        result = await db.execute(select(AgentMessage).order_by(AgentMessage.created_at.desc()).limit(100))
        msgs = result.scalars().all()
    return [{"id": m.id, "sender": m.sender, "recipient": m.recipient,
             "type": m.message_type, "content": m.content[:200],
             "read": m.read, "created_at": m.created_at.isoformat()} for m in msgs]


@router.get("/tasks")
async def get_tasks(status: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(AgentTask)
    if status:
        q = q.where(AgentTask.status == status)
    q = q.order_by(AgentTask.created_at.desc()).limit(100)
    result = await db.execute(q)
    tasks = result.scalars().all()
    return [{"id": t.id, "type": t.task_type, "status": t.status, "agent": t.assigned_agent,
             "retry_count": t.retry_count, "duration_ms": t.duration_ms,
             "created_at": t.created_at.isoformat()} for t in tasks]


@router.get("/memory")
async def get_agent_memory(agent_id: str, db: AsyncSession = Depends(get_db)):
    from ...models.agent import AgentMemory
    result = await db.execute(
        select(AgentMemory).where(AgentMemory.agent_id == agent_id).order_by(AgentMemory.importance.desc()).limit(50)
    )
    memories = result.scalars().all()
    return [{"key": m.key, "type": m.memory_type, "value": m.value[:200],
             "importance": m.importance, "created_at": m.created_at.isoformat()} for m in memories]


@router.get("/metrics")
async def get_agent_metrics(agent_id: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(AgentMetric)
    if agent_id:
        q = q.where(AgentMetric.agent_id == agent_id)
    q = q.order_by(AgentMetric.created_at.desc()).limit(100)
    result = await db.execute(q)
    metrics = result.scalars().all()
    return [{"id": m.id, "agent_id": m.agent_id, "type": m.metric_type,
             "value": m.value, "unit": m.unit} for m in metrics]
