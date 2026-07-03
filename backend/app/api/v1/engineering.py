import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.engineering import EngineeringPlan, EngineeringTask, EngineeringPatch, EngineeringValidation, EngineeringRepair, EngineeringQuality, EngineeringApproval, EngineeringMetric, EngineeringReport
from ...engineering.goal.analyzer import GoalAnalyzer
from ...engineering.validator.service import ValidationService
from ...engineering.repair.service import RepairService
from ...engineering.quality.gates import QualityGatesService
from ...engineering.documentation.service import DocumentationService
from ...engineering.risk.engine import RiskEngine
from ...websocket.manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/engineering", tags=["engineering"])


@router.post("/plan")
async def create_plan(data: dict, db: AsyncSession = Depends(get_db)):
    analyzer = GoalAnalyzer()
    goal = data.get("goal", "")
    if not goal:
        raise HTTPException(400, "Goal required")

    analysis = await analyzer.analyze(goal)

    risk_engine = RiskEngine()
    risk = risk_engine.classify(goal, analysis["goal_type"], analysis.get("affected_files", []))

    plan = EngineeringPlan(
        goal=goal, goal_type=analysis["goal_type"],
        risk_level=risk["level"], estimated_hours=analysis["estimated_hours"],
        affected_files=analysis["affected_files"],
        impact_analysis=analysis.get("impact_analysis", {}),
        architecture_check=analysis.get("architecture_check", {}),
        requires_approval=risk["requires_approval"],
        status="planning",
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    for i, t in enumerate(analysis.get("tasks", [])):
        task = EngineeringTask(
            plan_id=plan.id, agent_role=t["role"],
            description=t["description"], position=i,
            files=analysis.get("affected_files", []),
        )
        db.add(task)
    await db.commit()

    await ws_manager.broadcast("plan_ready", {"plan_id": plan.id, "goal": goal})
    return {"plan_id": plan.id, "goal": goal, "goal_type": plan.goal_type,
            "risk_level": risk["level"], "requires_approval": risk["requires_approval"],
            "tasks": analysis.get("tasks", []), "estimated_hours": plan.estimated_hours}


@router.post("/execute")
async def execute_plan(data: dict, db: AsyncSession = Depends(get_db)):
    plan_id = data.get("plan_id", "")
    if not plan_id:
        raise HTTPException(400, "plan_id required")

    plan = await db.get(EngineeringPlan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    if plan.requires_approval and not plan.approved:
        return {"status": "requires_approval", "message": "Plan requires approval before execution"}

    plan.status = "executing"
    await db.commit()

    result = await db.execute(
        select(EngineeringTask).where(EngineeringTask.plan_id == plan_id).order_by(EngineeringTask.position)
    )
    tasks = result.scalars().all()

    outputs = []
    for task in tasks:
        task.status = "running"
        await db.commit()
        patch = {"operation": "modify", "description": task.description, "status": "pending"}
        outputs.append({"task_id": task.id, "role": task.agent_role, "status": "running"})
        task.status = "completed"
        await db.commit()

    plan.status = "completed"
    await db.commit()

    await ws_manager.broadcast("workflow_completed", {"plan_id": plan_id})
    return {"plan_id": plan_id, "status": "completed", "tasks": len(tasks), "outputs": outputs}


@router.post("/validate")
async def validate_plan(data: dict, db: AsyncSession = Depends(get_db)):
    plan_id = data.get("plan_id", "")
    if not plan_id:
        raise HTTPException(400, "plan_id required")

    validator = ValidationService(db)
    results = await validator.validate(plan_id, data.get("task_id"))
    all_passed = all(r.passed for r in results)

    await ws_manager.broadcast("validation_done", {"plan_id": plan_id, "passed": all_passed})
    return [{"check": r.check_type, "passed": r.passed, "status": r.status} for r in results]


@router.post("/repair")
async def repair_task(data: dict, db: AsyncSession = Depends(get_db)):
    plan_id = data.get("plan_id", "")
    task_id = data.get("task_id", "")
    failure = data.get("failure", "Unknown failure")
    iteration = data.get("iteration", 1)

    repair_svc = RepairService(db)
    repair = await repair_svc.repair(plan_id, task_id, failure, iteration)

    await ws_manager.broadcast("repair_done", {"plan_id": plan_id, "task_id": task_id, "iteration": iteration, "success": repair.success})
    return {"id": repair.id, "iteration": repair.iteration, "success": repair.success, "fix": repair.fix}


@router.post("/review")
async def review_plan(data: dict, db: AsyncSession = Depends(get_db)):
    plan_id = data.get("plan_id", "")
    if not plan_id:
        raise HTTPException(400, "plan_id required")

    quality = QualityGatesService(db)
    results = await quality.run_all(plan_id)
    passed = await quality.all_passed(plan_id)

    return {"plan_id": plan_id, "passed": passed, "gates": [{"type": r.quality_type, "passed": r.passed, "score": r.score} for r in results]}


@router.post("/document")
async def update_documentation(data: dict, db: AsyncSession = Depends(get_db)):
    plan_id = data.get("plan_id", "")
    if not plan_id:
        raise HTTPException(400, "plan_id required")

    plan = await db.get(EngineeringPlan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    docs = DocumentationService()
    changes = await docs.update(plan_id, plan.goal, plan.affected_files or [])

    report = EngineeringReport(plan_id=plan_id, report_type="documentation", content=str(changes))
    db.add(report)
    await db.commit()

    return {"plan_id": plan_id, "changes": changes}


@router.get("/tasks")
async def get_tasks(status: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(EngineeringTask)
    if status:
        q = q.where(EngineeringTask.status == status)
    q = q.order_by(EngineeringTask.created_at.desc()).limit(100)
    result = await db.execute(q)
    tasks = result.scalars().all()
    return [{"id": t.id, "plan_id": t.plan_id, "role": t.agent_role, "status": t.status, "description": t.description[:100]} for t in tasks]


@router.get("/reports")
async def get_reports(plan_id: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(EngineeringReport)
    if plan_id:
        q = q.where(EngineeringReport.plan_id == plan_id)
    q = q.order_by(EngineeringReport.created_at.desc()).limit(50)
    result = await db.execute(q)
    reports = result.scalars().all()
    return [{"id": r.id, "plan_id": r.plan_id, "type": r.report_type, "content": r.content[:200]} for r in reports]


@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EngineeringMetric).order_by(EngineeringMetric.created_at.desc()).limit(100)
    )
    metrics = result.scalars().all()
    return [{"type": m.metric_type, "value": m.value, "unit": m.unit} for m in metrics]


@router.get("/quality")
async def get_quality(plan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EngineeringQuality).where(EngineeringQuality.plan_id == plan_id)
    )
    checks = result.scalars().all()
    return [{"type": q.quality_type, "passed": q.passed, "score": q.score} for q in checks]


@router.post("/approve")
async def approve_plan(data: dict, db: AsyncSession = Depends(get_db)):
    plan_id = data.get("plan_id", "")
    if not plan_id:
        raise HTTPException(400, "plan_id required")
    plan = await db.get(EngineeringPlan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    plan.approved = True
    plan.approved_by = data.get("approved_by", "system")
    plan.status = "approved"

    approval = EngineeringApproval(plan_id=plan_id, request_type="execution", reason="Approved by user", status="approved")
    db.add(approval)
    await db.commit()

    return {"plan_id": plan_id, "status": "approved"}
