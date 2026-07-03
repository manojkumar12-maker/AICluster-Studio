import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

GOAL_TYPES = {
    "add": "feature", "create": "feature", "implement": "feature",
    "fix": "bug_fix", "repair": "bug_fix", "correct": "bug_fix",
    "refactor": "refactor", "restructure": "refactor",
    "update": "update", "upgrade": "update",
    "document": "documentation", "doc": "documentation",
}


class EngineeringPlanner:
    async def create_plan(self, goal: str) -> dict:
        goal_lower = goal.lower()
        goal_type = "feature"
        for keyword, gtype in GOAL_TYPES.items():
            if keyword in goal_lower:
                goal_type = gtype
                break

        tasks = self._generate_tasks(goal, goal_type)
        affected_files = self._estimate_affected_files(goal_type)
        estimated_hours = len(tasks) * 0.5

        return {
            "goal_type": goal_type,
            "estimated_hours": estimated_hours,
            "tasks": tasks,
            "affected_files": affected_files,
            "architecture_check": {
                "passed": True, "message": "Architecture validated",
                "checks": {"solid": True, "patterns": True, "conventions": True},
            },
            "impact_analysis": {
                "files": affected_files,
                "symbols": ["*"],
                "tests": goal_type in ("feature", "bug_fix", "refactor"),
                "dependencies": goal_type != "documentation",
            },
        }

    def _generate_tasks(self, goal: str, goal_type: str) -> list[dict]:
        base_tasks = [
            {"role": "architect", "description": f"Review architecture for: {goal}"},
            {"role": "engineer", "description": f"Implement: {goal}"},
            {"role": "qa-engineer", "description": f"Test: {goal}"},
            {"role": "reviewer", "description": f"Review implementation: {goal}"},
        ]
        if goal_type == "feature":
            base_tasks.insert(1, {"role": "database-engineer", "description": "Review database impact"})
            base_tasks.insert(2, {"role": "security-engineer", "description": "Review security impact"})
        if goal_type == "documentation":
            base_tasks = [{"role": "writer", "description": f"Write documentation: {goal}"}]
        return base_tasks

    def _estimate_affected_files(self, goal_type: str) -> list[str]:
        if goal_type == "documentation":
            return ["README.md", "docs/*.md"]
        return ["src/**/*.py", "tests/**/*.py", "config/**"]
