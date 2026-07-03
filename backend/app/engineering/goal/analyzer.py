import logging
from ..planner.service import EngineeringPlanner

logger = logging.getLogger(__name__)

RISK_KEYWORDS = {
    "delete": "high", "remove": "high", "migration": "critical",
    "auth": "high", "security": "critical", "password": "critical",
    "database": "high", "schema": "high", "api": "medium",
    "refactor": "medium", "config": "medium",
}


class GoalAnalyzer:
    def __init__(self):
        self.planner = EngineeringPlanner()

    async def analyze(self, goal: str) -> dict:
        goal_lower = goal.lower()
        risk = "low"
        for keyword, level in RISK_KEYWORDS.items():
            if keyword in goal_lower:
                if level == "critical":
                    risk = "critical"
                elif level == "high" and risk != "critical":
                    risk = "high"
                elif level == "medium" and risk not in ("critical", "high"):
                    risk = "medium"

        requires_approval = risk in ("high", "critical")

        plan = await self.planner.create_plan(goal)

        return {
            "goal": goal,
            "goal_type": plan.get("goal_type", "feature"),
            "risk_level": risk,
            "requires_approval": requires_approval,
            "estimated_hours": plan.get("estimated_hours", 1.0),
            "affected_files": plan.get("affected_files", []),
            "tasks": plan.get("tasks", []),
            "architecture_check": plan.get("architecture_check", {}),
            "impact_analysis": plan.get("impact_analysis", {}),
        }
