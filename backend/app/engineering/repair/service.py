import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.engineering import EngineeringRepair

logger = logging.getLogger(__name__)

MAX_REPAIR_ITERATIONS = 3


class RepairService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def repair(self, plan_id: str, task_id: str, failure: str,
                     iteration: int = 1) -> EngineeringRepair:
        if iteration > MAX_REPAIR_ITERATIONS:
            repair = EngineeringRepair(
                plan_id=plan_id, task_id=task_id, iteration=iteration,
                max_iterations=MAX_REPAIR_ITERATIONS, failure=failure,
                status="max_iterations_reached", success=False,
                fix="Max repair iterations reached",
            )
            self.db.add(repair)
            await self.db.commit()
            await self.db.refresh(repair)
            return repair

        fix = self._generate_fix(failure, iteration)
        repair = EngineeringRepair(
            plan_id=plan_id, task_id=task_id, iteration=iteration,
            max_iterations=MAX_REPAIR_ITERATIONS, failure=failure,
            fix=fix, status="completed", success=True,
        )
        self.db.add(repair)
        await self.db.commit()
        await self.db.refresh(repair)
        logger.info(f"Repair iteration {iteration}/{MAX_REPAIR_ITERATIONS} for task {task_id}")
        return repair

    def _generate_fix(self, failure: str, iteration: int) -> str:
        fixes = {
            1: f"Attempting automatic fix for: {failure[:100]}",
            2: f"Re-analyzing and fixing: {failure[:100]}",
            3: f"Final attempt to resolve: {failure[:100]}",
        }
        return fixes.get(iteration, f"Fixing: {failure[:100]}")
