import logging
from ...models.engineering import EngineeringApproval

logger = logging.getLogger(__name__)

REQUIRES_APPROVAL_TYPES = ["delete", "migration", "auth", "security", "config", "bulk_edit", "refactor"]


class RiskEngine:
    def __init__(self):
        pass

    def classify(self, goal: str, goal_type: str, affected_files: list[str]) -> dict:
        risk_level = "low"
        reasons = []

        goal_lower = goal.lower()
        for keyword in REQUIRES_APPROVAL_TYPES:
            if keyword in goal_lower:
                risk_level = "high" if risk_level != "critical" else risk_level
                reasons.append(f"Contains '{keyword}' keyword")

        if any("migration" in f.lower() for f in affected_files):
            risk_level = "critical"
            reasons.append("Affects migration files")

        if any("security" in f.lower() or "auth" in f.lower() for f in affected_files):
            if risk_level != "critical":
                risk_level = "high"
                reasons.append("Affects security/auth files")

        if len(affected_files) > 20:
            if risk_level == "low":
                risk_level = "medium"
                reasons.append(f"Large number of files affected ({len(affected_files)})")

        return {"level": risk_level, "reasons": reasons, "requires_approval": risk_level in ("high", "critical")}

    def create_approval_request(self, plan_id: str, request_type: str, reason: str) -> EngineeringApproval:
        return EngineeringApproval(
            plan_id=plan_id, request_type=request_type, reason=reason, status="pending",
        )
