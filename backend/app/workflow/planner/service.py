import logging
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.workflow import Workflow, WorkflowTask, TaskDependency
from ..state.states import TASK_TYPES

logger = logging.getLogger(__name__)


class WorkflowPlanner:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def plan(self, workflow: Workflow, tasks_config: list[dict]) -> list[WorkflowTask]:
        tasks = []
        for i, tc in enumerate(tasks_config):
            task = WorkflowTask(
                workflow_id=workflow.id,
                name=tc.get("name", f"Task {i+1}"),
                task_type=tc.get("type", "custom"),
                payload=tc.get("payload", {}),
                priority=tc.get("priority", workflow.priority),
                timeout_seconds=tc.get("timeout", 300),
                position=i,
                status="CREATED",
            )
            self.db.add(task)
            tasks.append(task)
        await self.db.flush()

        deps_list = []
        for i, tc in enumerate(tasks_config):
            depends_on = tc.get("depends_on", [])
            for dep_id_ref in depends_on:
                dep_task = next((t for t in tasks if t.name == dep_id_ref or t.position == dep_id_ref), None)
                if dep_task and dep_task.id != tasks[i].id:
                    dep = TaskDependency(task_id=tasks[i].id, depends_on_id=dep_task.id)
                    self.db.add(dep)
                    deps_list.append(dep)

        workflow.total_tasks = len(tasks)
        workflow.status = "QUEUED"
        await self.db.commit()

        for task in tasks:
            await self.db.refresh(task)
        logger.info(f"Workflow {workflow.id}: planned {len(tasks)} tasks, {len(deps_list)} dependencies")
        return tasks

    async def generate_dag(self, tasks: list[WorkflowTask]) -> dict:
        nodes = []
        edges = []
        for t in tasks:
            nodes.append({"id": t.id, "name": t.name, "type": t.task_type, "status": t.status, "position": t.position})
        for t in tasks:
            result = await self.db.execute(select(TaskDependency).where(TaskDependency.task_id == t.id))
            for dep in result.scalars():
                edges.append({"from": dep.depends_on_id, "to": dep.task_id})
        return {"nodes": nodes, "edges": edges}

    async def estimate_duration(self, tasks: list[WorkflowTask]) -> float:
        estimates = {"echo": 1, "sleep": 10, "dir_scan": 30, "hash_file": 15, "count_files": 20, "compress": 60, "extract": 30, "report": 10, "custom": 30}
        parallel_paths: dict[int, float] = {}
        for t in tasks:
            est = estimates.get(t.task_type, 30)
            parallel_paths[t.position] = parallel_paths.get(t.position, 0) + est
        return max(parallel_paths.values()) if parallel_paths else sum(estimates.get(t.task_type, 30) for t in tasks)
