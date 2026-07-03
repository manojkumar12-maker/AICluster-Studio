import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.agent import Agent, AgentTask

logger = logging.getLogger(__name__)


class PlanningService:
    ROLES_BY_TASK = {
        "backend": ["architect", "backend-engineer", "database-engineer", "qa-engineer", "documentation-writer"],
        "frontend": ["architect", "frontend-engineer", "qa-engineer", "documentation-writer"],
        "api": ["architect", "backend-engineer", "security-engineer", "qa-engineer"],
        "database": ["architect", "database-engineer", "backend-engineer"],
        "fullstack": ["architect", "backend-engineer", "frontend-engineer", "database-engineer",
                       "security-engineer", "qa-engineer", "documentation-writer"],
        "default": ["architect", "engineer", "qa-engineer", "reviewer"],
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_plan(self, workflow_id: str, request: str, request_type: str = "default") -> list[dict]:
        plan = []
        roles = self.ROLES_BY_TASK.get(request_type, self.ROLES_BY_TASK["default"])
        for i, role in enumerate(roles):
            agents = await self.db.execute(
                select(Agent).where(Agent.role == role, Agent.status == "idle").limit(1)
            )
            agent = agents.scalar_one_or_none()
            plan.append({
                "position": i,
                "role": role,
                "agent_id": agent.id if agent else None,
                "agent_name": agent.name if agent else role,
                "description": f"Execute {role} tasks for: {request[:100]}",
                "status": "planned",
                "depends_on": list(range(i)) if i > 0 else [],
            })
        plan.append({
            "position": len(roles),
            "role": "reviewer",
            "agent_name": "reviewer",
            "description": "Review all outputs",
            "status": "planned",
            "depends_on": list(range(len(roles))),
        })
        plan.append({
            "position": len(roles) + 1,
            "role": "merger",
            "agent_name": "merger",
            "description": "Merge all outputs",
            "status": "planned",
            "depends_on": [len(roles)],
        })
        return plan

    async def estimate_duration(self, plan: list[dict]) -> int:
        return len(plan) * 30
