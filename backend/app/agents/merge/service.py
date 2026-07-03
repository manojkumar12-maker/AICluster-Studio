import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.agent import AgentMerge, AgentTask

logger = logging.getLogger(__name__)


class MergeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def merge(self, workflow_id: str, task_ids: list[str]) -> AgentMerge:
        outputs = []
        for tid in task_ids:
            task = await self.db.get(AgentTask, tid)
            if task and task.output:
                outputs.append({"task_id": tid, "role": task.task_type, "output": task.output})

        merged = AgentMerge(
            workflow_id=workflow_id, source_agents=task_ids,
            status="completed", input_artifacts=outputs,
            output={"merged_result": self._combine(outputs)},
            resolved=True,
        )
        self.db.add(merged)
        await self.db.commit()
        await self.db.refresh(merged)
        return merged

    def _combine(self, outputs: list[dict]) -> str:
        parts = []
        for o in outputs:
            role = o.get("role", "unknown")
            result = o.get("output", {}).get("result", "")
            parts.append(f"## {role.upper()}\n{result}")
        return "\n\n".join(parts)
