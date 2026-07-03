import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.agent import Agent, AgentTask, AgentMessage, AgentReview, AgentMerge, AgentMetric
from ..registry.service import AgentRegistry
from ..planner.service import PlanningService
from ..communication.service import CommunicationService
from ..review.service import ReviewService
from ..merge.service import MergeService
from ...websocket.manager import ws_manager

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.registry = AgentRegistry(db)
        self.planner = PlanningService(db)
        self.communication = CommunicationService(db)
        self.reviewer = ReviewService(db)
        merger = MergeService(db)

    async def run(self, request: str, request_type: str = "default",
                  workflow_id: str | None = None) -> dict:
        plan = await self.planner.create_plan(workflow_id or "", request, request_type)

        tasks = []
        for step in plan:
            task = AgentTask(
                workflow_id=workflow_id, assigned_agent=step.get("agent_id"),
                task_type=step["role"], status="pending", input={
                    "request": request, "position": step["position"],
                    "description": step["description"],
                    "depends_on": step.get("depends_on", []),
                },
            )
            self.db.add(task)
            tasks.append(task)

        await self.db.flush()
        for task in tasks:
            await self.db.refresh(task)
        await self.db.commit()

        await ws_manager.broadcast("agent_workflow_started", {
            "workflow_id": workflow_id, "tasks": len(tasks),
        })
        logger.info(f"Orchestrator: {len(tasks)} tasks planned for workflow {workflow_id}")
        return {"plan": plan, "tasks": [{"id": t.id, "role": t.task_type, "status": t.status} for t in tasks]}

    async def run_sync(self, request: str, request_type: str = "default",
                       workflow_id: str | None = None) -> dict:
        plan = await self.planner.create_plan(workflow_id or "", request, request_type)
        outputs = []
        for i, step in enumerate(plan):
            task = AgentTask(
                workflow_id=workflow_id, assigned_agent=step.get("agent_id"),
                task_type=step["role"], status="running",
                input={"request": request, "position": step["position"]},
                started_at=datetime.now(timezone.utc),
            )
            self.db.add(task)
            await self.db.flush()
            await self.db.refresh(task)

            agent_name = step.get("agent_name", step["role"])
            output = f"[{agent_name}] Processing: {step['description']}"
            task.status = "completed"
            task.output = {"result": output}
            task.finished_at = datetime.now(timezone.utc)
            outputs.append({"role": step["role"], "agent": agent_name, "output": output})
            await self.db.commit()
            await ws_manager.broadcast("agent_task_completed", {
                "task_id": task.id, "agent": agent_name, "status": "completed",
            })

        return {
            "request": request,
            "steps": len(outputs),
            "outputs": outputs,
            "summary": f"Completed {len(outputs)} agent tasks",
        }
