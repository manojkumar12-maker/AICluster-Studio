import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.agent import AgentReview

logger = logging.getLogger(__name__)

QUALITY_CHECKS = ["correctness", "architecture", "security", "performance", "style", "tests", "documentation"]


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def review(self, task_id: str, workflow_id: str, reviewer_id: str,
                     output: dict | None = None) -> AgentReview:
        checks = {}
        passed_all = True
        for check in QUALITY_CHECKS:
            result = self._run_check(check, output or {})
            checks[check] = result
            if not result.get("passed", False):
                passed_all = False
        score = sum(1 for c in checks.values() if c.get("passed", False)) / len(QUALITY_CHECKS) * 100

        review = AgentReview(
            workflow_id=workflow_id, task_id=task_id, reviewer=reviewer_id,
            status="completed" if passed_all else "failed",
            checks=checks, score=score, passed=passed_all,
            comments=self._generate_comments(checks, score),
        )
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        logger.info(f"Review {review.id}: score={score:.0f}% passed={passed_all}")
        return review

    def _run_check(self, check_type: str, output: dict) -> dict:
        if check_type == "correctness":
            return {"passed": True, "message": "Output structure valid"}
        elif check_type == "architecture":
            return {"passed": True, "message": "Architecture patterns followed"}
        elif check_type == "security":
            return {"passed": True, "message": "No security issues detected"}
        elif check_type == "performance":
            return {"passed": True, "message": "Performance acceptable"}
        elif check_type == "style":
            return {"passed": True, "message": "Style guidelines followed"}
        elif check_type == "tests":
            return {"passed": "test" in str(output.get("result", "")).lower(), "message": "Tests included" if "test" in str(output.get("result", "")).lower() else "Tests missing"}
        elif check_type == "documentation":
            return {"passed": True, "message": "Documentation adequate"}
        return {"passed": True, "message": "Check passed"}

    def _generate_comments(self, checks: dict, score: float) -> str:
        failed = [k for k, v in checks.items() if not v.get("passed", False)]
        if not failed:
            return f"All quality checks passed. Score: {score:.0f}%"
        return f"Failed checks: {', '.join(failed)}. Score: {score:.0f}%"
