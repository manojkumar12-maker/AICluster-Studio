import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.agent import Agent

logger = logging.getLogger(__name__)


class AgentRegistry:
    _agents: dict[str, type] = {}

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, name: str, role: str, description: str | None = None,
                       capabilities: list | None = None, permissions: list | None = None,
                       allowed_tools: list | None = None, model_preference: str | None = None,
                       priority: int = 0) -> Agent:
        existing = await self.db.execute(select(Agent).where(Agent.name == name))
        agent = existing.scalar_one_or_none()
        if agent:
            agent.role = role
            agent.description = description or agent.description
            agent.status = "idle"
            await self.db.commit()
            await self.db.refresh(agent)
            return agent
        agent = Agent(
            name=name, role=role, description=description,
            capabilities=capabilities or [], permissions=permissions or [],
            allowed_tools=allowed_tools or [], model_preference=model_preference,
            priority=priority, status="idle",
        )
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)
        logger.info(f"Agent registered: {name} ({role})")
        return agent

    async def get(self, agent_id: str) -> Agent | None:
        return await self.db.get(Agent, agent_id)

    async def find_by_role(self, role: str) -> list[Agent]:
        result = await self.db.execute(
            select(Agent).where(Agent.role == role, Agent.status == "idle").order_by(Agent.priority)
        )
        return list(result.scalars().all())

    async def find_capable(self, capability: str) -> list[Agent]:
        result = await self.db.execute(
            select(Agent).where(Agent.status == "idle").order_by(Agent.priority)
        )
        all_agents = result.scalars().all()
        return [a for a in all_agents if capability in (a.capabilities or [])]

    async def set_status(self, agent_id: str, status: str):
        agent = await self.db.get(Agent, agent_id)
        if agent:
            agent.status = status
            await self.db.commit()

    async def list_all(self) -> list[Agent]:
        result = await self.db.execute(select(Agent).order_by(Agent.role, Agent.priority))
        return list(result.scalars().all())

    async def seed_default_agents(self):
        defaults = [
            ("planner", "planner", "Breaks complex requests into tasks and creates execution DAGs", ["planning", "decomposition", "dag_creation"]),
            ("architect", "architect", "Designs system architecture and component relationships", ["architecture", "design", "code_review"]),
            ("backend-engineer", "engineer", "Implements backend services, APIs, and database logic", ["backend", "api", "database", "python", "sql"]),
            ("frontend-engineer", "engineer", "Implements user interfaces and frontend logic", ["frontend", "ui", "react", "typescript"]),
            ("database-engineer", "engineer", "Designs database schemas and queries", ["database", "sql", "schema_design", "migrations"]),
            ("devops-engineer", "engineer", "Manages deployment, infrastructure, and CI/CD", ["devops", "deployment", "ci_cd", "docker"]),
            ("security-engineer", "engineer", "Reviews code for security vulnerabilities", ["security", "audit", "vulnerability_scan"]),
            ("qa-engineer", "qa", "Creates and runs tests, verifies quality", ["testing", "quality", "test_creation"]),
            ("documentation-writer", "writer", "Writes documentation and technical guides", ["documentation", "writing", "technical_writing"]),
            ("reviewer", "reviewer", "Reviews agent outputs for correctness and quality", ["review", "code_review", "quality_assurance"]),
            ("merger", "merger", "Merges outputs from multiple agents into final result", ["merge", "integration", "conflict_resolution"]),
            ("project-manager", "manager", "Coordinates agent activities and tracks progress", ["management", "coordination", "planning"]),
        ]
        for name, role, desc, caps in defaults:
            await self.register(name=name, role=role, description=desc, capabilities=caps)
