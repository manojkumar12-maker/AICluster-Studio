from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.worker import Worker
from ..models.log import SystemLog
from ..config import settings


class WorkerManagerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, name: str, hostname: str, ip: str) -> Worker:
        existing = await self.db.execute(
            select(Worker).where(Worker.worker_name == name)
        )
        worker = existing.scalar_one_or_none()

        if worker:
            worker.ip = ip
            worker.hostname = hostname
            worker.status = "online"
            worker.last_seen = datetime.now(timezone.utc)
        else:
            worker = Worker(
                worker_name=name,
                hostname=hostname,
                ip=ip,
                status="online",
                last_seen=datetime.now(timezone.utc),
            )
            self.db.add(worker)

        await self.db.commit()
        await self.db.refresh(worker)

        log = SystemLog(
            level="INFO",
            message=f"Worker '{name}' registered from {ip}",
            source="worker_manager",
        )
        self.db.add(log)
        await self.db.commit()

        return worker

    async def process_heartbeat(
        self, worker_id: str, cpu: float, ram: float, disk: float,
        temperature: float | None, busy: bool, network_speed: float
    ) -> Worker:
        result = await self.db.execute(select(Worker).where(Worker.id == worker_id))
        worker = result.scalar_one_or_none()
        if not worker:
            raise ValueError(f"Worker {worker_id} not found")

        worker.cpu_percent = cpu
        worker.ram_percent = ram
        worker.disk_percent = disk
        worker.temperature = temperature
        worker.network_speed = network_speed
        worker.status = "busy" if busy else "online"
        worker.last_seen = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(worker)
        return worker

    async def mark_offline_workers(self):
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=settings.worker_timeout_seconds
        )
        result = await self.db.execute(
            select(Worker).where(
                Worker.last_seen < cutoff,
                Worker.status.notin_(["offline", "disabled"]),
            )
        )
        workers = result.scalars().all()
        for w in workers:
            w.status = "offline"
            w.current_job = None
            log = SystemLog(
                level="WARNING",
                message=f"Worker '{w.worker_name}' marked offline (heartbeat timeout)",
                source="worker_manager",
            )
            self.db.add(log)
        if workers:
            await self.db.commit()
        return len(workers)

    async def get_all(self) -> list[Worker]:
        result = await self.db.execute(
            select(Worker).order_by(Worker.worker_name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, worker_id: str) -> Worker | None:
        result = await self.db.execute(select(Worker).where(Worker.id == worker_id))
        return result.scalar_one_or_none()

    async def pause(self, worker_id: str) -> Worker:
        result = await self.db.execute(select(Worker).where(Worker.id == worker_id))
        worker = result.scalar_one_or_none()
        if not worker:
            raise ValueError("Worker not found")
        worker.is_paused = True
        if worker.status == "online":
            worker.status = "paused"
        await self.db.commit()
        await self.db.refresh(worker)
        return worker

    async def resume(self, worker_id: str) -> Worker:
        result = await self.db.execute(select(Worker).where(Worker.id == worker_id))
        worker = result.scalar_one_or_none()
        if not worker:
            raise ValueError("Worker not found")
        worker.is_paused = False
        worker.status = "online"
        await self.db.commit()
        await self.db.refresh(worker)
        return worker

    async def get_dashboard(self) -> dict:
        total = await self.db.scalar(select(func.count(Worker.id)))
        online = await self.db.scalar(
            select(func.count(Worker.id)).where(Worker.status == "online")
        )
        offline = await self.db.scalar(
            select(func.count(Worker.id)).where(Worker.status == "offline")
        )
        busy = await self.db.scalar(
            select(func.count(Worker.id)).where(Worker.status == "busy")
        )
        idle = (online or 0) - (busy or 0)

        avg_cpu = await self.db.scalar(
            select(func.coalesce(func.avg(Worker.cpu_percent), 0))
        )
        avg_ram = await self.db.scalar(
            select(func.coalesce(func.avg(Worker.ram_percent), 0))
        )

        return {
            "total_workers": total or 0,
            "online": online or 0,
            "offline": offline or 0,
            "idle": max(idle, 0),
            "busy": busy or 0,
            "average_cpu": round(float(avg_cpu or 0), 1),
            "average_ram": round(float(avg_ram or 0), 1),
        }

    async def count(self) -> int:
        return await self.db.scalar(select(func.count(Worker.id))) or 0
