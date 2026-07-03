import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    worker_name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    ip: Mapped[str] = mapped_column(String(45), nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="offline", index=True)
    cpu_percent: Mapped[float] = mapped_column(Float, default=0.0)
    ram_percent: Mapped[float] = mapped_column(Float, default=0.0)
    disk_percent: Mapped[float] = mapped_column(Float, default=0.0)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    network_speed: Mapped[float] = mapped_column(Float, default=0.0)

    current_job: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[str] = mapped_column(String(32), default="1.0.0")

    cpu_limit: Mapped[float] = mapped_column(Float, default=25.0)
    ram_limit: Mapped[float] = mapped_column(Float, default=8.0)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)

    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
