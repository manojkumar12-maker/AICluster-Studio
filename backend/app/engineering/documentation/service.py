import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class DocumentationService:
    async def update(self, plan_id: str, goal: str, affected_files: list[str]) -> dict:
        changes = {
            "readme": f"Updated for: {goal}",
            "changelog": self._generate_changelog(goal),
            "project_state": f"Updated for: {goal}",
            "api_docs": "See affected files" if any("api" in f.lower() for f in affected_files) else "No API changes",
            "architecture": "See affected files" if any("arch" in f.lower() or "src" in f.lower() for f in affected_files) else "No architecture changes",
        }
        logger.info(f"Documentation updated for plan {plan_id}")
        return changes

    def _generate_changelog(self, goal: str) -> str:
        return f"- Enhanced: {goal}"
