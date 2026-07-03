import csv
import io
import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select, func, or_, and_, text, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditLog, AuditSetting, AuditExport, AuditRetention
from .schemas import AuditSearchRequest, AuditStatistics, AuditSettingsResponse
from .events import AuditEvent

logger = logging.getLogger(__name__)


class AuditService:
    EXPORT_DIR = Path(__file__).resolve().parent.parent.parent / "exports"
    CATEGORIES = [
        "authentication", "worker", "workflow", "repository", "ai_runtime",
        "engineering", "plugin", "studio", "settings", "backup", "restore",
        "deployment", "monitoring", "system", "security", "user", "scheduler",
    ]
    EVENT_TYPES = [
        "LOGIN", "LOGOUT", "LOGIN_FAILED", "TOKEN_REFRESH",
        "WORKFLOW_CREATED", "WORKFLOW_STARTED", "WORKFLOW_COMPLETED",
        "WORKFLOW_FAILED", "WORKFLOW_CANCELLED",
        "WORKER_REGISTERED", "WORKER_DISCONNECTED", "WORKER_RECONNECTED",
        "WORKER_RESTARTED", "WORKER_UPDATED",
        "PLUGIN_INSTALLED", "PLUGIN_UPDATED", "PLUGIN_ENABLED",
        "PLUGIN_DISABLED", "PLUGIN_REMOVED",
        "MODEL_LOADED", "MODEL_UNLOADED", "MODEL_SWITCHED",
        "AI_CHAT", "TOOL_CALL", "TOOL_RESULT",
        "REPOSITORY_SCANNED", "REPOSITORY_INDEXED",
        "ENGINEERING_PLAN", "PATCH_CREATED", "PATCH_APPLIED",
        "VALIDATION_STARTED", "VALIDATION_COMPLETED",
        "BACKUP_CREATED", "BACKUP_RESTORED",
        "CONFIG_CHANGED", "SYSTEM_STARTED", "SYSTEM_STOPPED",
        "ERROR", "WARNING", "CUSTOM_EVENT",
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, event_type: str, category: str = "system", severity: str = "INFO",
                  message: str | None = None, user_id: str | None = None,
                  username: str | None = None, worker_id: str | None = None,
                  workflow_id: str | None = None, repository_id: str | None = None,
                  plugin_id: str | None = None, agent_id: str | None = None,
                  session_id: str | None = None, resource_type: str | None = None,
                  resource_id: str | None = None, action: str | None = None,
                  status: str | None = None, duration_ms: float | None = None,
                  ip_address: str | None = None, extra: dict | None = None,
                  old_value: dict | None = None, new_value: dict | None = None,
                  request_id: str | None = None, trace_id: str | None = None) -> AuditLog:
        log_entry = AuditLog(
            event_type=event_type, category=category, severity=severity,
            message=message, user_id=user_id, username=username,
            worker_id=worker_id, workflow_id=workflow_id,
            repository_id=repository_id, plugin_id=plugin_id, agent_id=agent_id,
            session_id=session_id, resource_type=resource_type, resource_id=resource_id,
            action=action, status=status, duration_ms=duration_ms,
            ip_address=ip_address, extra=extra or {},
            old_value=old_value or {}, new_value=new_value or {},
            request_id=request_id or str(uuid.uuid4()), trace_id=trace_id,
        )
        self.db.add(log_entry)
        try:
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            await self.db.rollback()
        return log_entry

    async def log_event(self, event: AuditEvent) -> AuditLog:
        return await self.log(
            event_type=event.event_type, category=event.category, severity=event.severity,
            message=event.message, user_id=event.user_id, username=event.username,
            worker_id=event.worker_id, workflow_id=event.workflow_id,
            repository_id=event.repository_id, plugin_id=event.plugin_id,
            agent_id=event.agent_id, session_id=event.session_id,
            resource_type=event.resource_type, resource_id=event.resource_id,
            action=event.action, status=event.status, duration_ms=event.duration_ms,
            ip_address=event.ip_address, extra=event.extra,
            old_value=event.old_value, new_value=event.new_value,
            request_id=event.request_id, trace_id=event.trace_id,
        )

    async def search(self, req: AuditSearchRequest) -> tuple[list[AuditLog], int]:
        q = select(AuditLog)
        conditions = []
        if req.date_from:
            conditions.append(AuditLog.timestamp >= req.date_from)
        if req.date_to:
            conditions.append(AuditLog.timestamp <= req.date_to)
        if req.category:
            conditions.append(AuditLog.category == req.category)
        if req.severity:
            conditions.append(AuditLog.severity == req.severity)
        if req.event_type:
            conditions.append(AuditLog.event_type == req.event_type)
        if req.username:
            conditions.append(AuditLog.username.ilike(f"%{req.username}%"))
        if req.worker_id:
            conditions.append(AuditLog.worker_id == req.worker_id)
        if req.workflow_id:
            conditions.append(AuditLog.workflow_id == req.workflow_id)
        if req.repository_id:
            conditions.append(AuditLog.repository_id == req.repository_id)
        if req.plugin_id:
            conditions.append(AuditLog.plugin_id == req.plugin_id)
        if req.status:
            conditions.append(AuditLog.status == req.status)
        if req.text:
            conditions.append(AuditLog.message.ilike(f"%{req.text}%"))
        if conditions:
            q = q.where(and_(*conditions))
        count_q = q
        total = (await self.db.execute(select(func.count()).select_from(count_q.subquery()))).scalar() or 0
        q = q.order_by(AuditLog.timestamp.desc()).offset(req.offset).limit(req.limit)
        result = await self.db.execute(q)
        return list(result.scalars().all()), total

    async def get_statistics(self) -> AuditStatistics:
        base = select(AuditLog)
        today = await self.db.execute(
            select(func.count()).select_from(
                base.where(AuditLog.timestamp >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)).subquery()
            )
        )
        week = await self.db.execute(
            select(func.count()).select_from(
                base.where(AuditLog.timestamp >= datetime.now(timezone.utc) - timedelta(days=7)).subquery()
            )
        )
        critical_count = (await self.db.execute(
            select(func.count()).select_from(base.where(AuditLog.severity == "CRITICAL").subquery())
        )).scalar() or 0
        error_count = (await self.db.execute(
            select(func.count()).select_from(base.where(AuditLog.severity == "ERROR").subquery())
        )).scalar() or 0
        warning_count = (await self.db.execute(
            select(func.count()).select_from(base.where(AuditLog.severity == "WARNING").subquery())
        )).scalar() or 0
        total = (await self.db.execute(select(func.count()).select_from(select(AuditLog).subquery()))).scalar() or 0
        by_cat = await self.db.execute(
            select(AuditLog.category, func.count()).group_by(AuditLog.category)
        )
        by_sev = await self.db.execute(
            select(AuditLog.severity, func.count()).group_by(AuditLog.severity)
        )
        return AuditStatistics(
            total_events=total,
            today=today.scalar() or 0,
            this_week=week.scalar() or 0,
            critical=critical_count,
            errors=error_count,
            warnings=warning_count,
            success_rate=((total - error_count - critical_count) / max(total, 1)) * 100,
            by_category={row.category: row[1] for row in by_cat},
            by_severity={row.severity: row[1] for row in by_sev},
        )

    async def export_logs(self, fmt: str = "csv", filters: dict | None = None) -> AuditExport:
        self.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_{timestamp}.{fmt}"
        filepath = self.EXPORT_DIR / filename

        result = await self.db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10000))
        logs = result.scalars().all()

        if fmt == "csv":
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "timestamp", "event_type", "category", "severity", "user_id", "username", "worker_id", "workflow_id", "repository_id", "plugin_id", "status", "duration_ms", "message"])
                for log in logs:
                    writer.writerow([log.id, log.timestamp.isoformat(), log.event_type, log.category, log.severity, log.user_id, log.username, log.worker_id, log.workflow_id, log.repository_id, log.plugin_id, log.status, log.duration_ms, log.message])
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump([{"id": l.id, "timestamp": l.timestamp.isoformat(), "event_type": l.event_type, "category": l.category, "severity": l.severity, "username": l.username, "message": l.message} for l in logs], f, indent=2)

        export = AuditExport(format=fmt, filename=filename, size_bytes=filepath.stat().st_size, status="completed", record_count=len(logs), filters=filters or {})
        self.db.add(export)
        await self.db.commit()
        return export

    async def purge(self, before: datetime | None = None) -> int:
        cutoff = before or (datetime.now(timezone.utc) - timedelta(days=90))
        result = await self.db.execute(select(func.count()).where(AuditLog.timestamp < cutoff))
        count = result.scalar() or 0
        await self.db.execute(delete(AuditLog).where(AuditLog.timestamp < cutoff))
        retention = AuditRetention(purged_before=cutoff, records_purged=count, status="completed")
        self.db.add(retention)
        await self.db.commit()
        return count

    async def get_settings(self) -> AuditSettingsResponse:
        result = await self.db.execute(select(AuditSetting).limit(1))
        setting = result.scalar_one_or_none()
        if not setting:
            return AuditSettingsResponse()
        return AuditSettingsResponse(
            retention_days=setting.retention_days, auto_purge_enabled=setting.auto_purge_enabled,
            export_format=setting.export_format, max_log_size_mb=setting.max_log_size_mb,
            notification_on_critical=setting.notification_on_critical,
        )

    async def update_settings(self, data: dict) -> AuditSettingsResponse:
        result = await self.db.execute(select(AuditSetting).limit(1))
        setting = result.scalar_one_or_none()
        if not setting:
            setting = AuditSetting()
            self.db.add(setting)
        for key, value in data.items():
            if hasattr(setting, key) and value is not None:
                setattr(setting, key, value)
        await self.db.commit()
        return await self.get_settings()
