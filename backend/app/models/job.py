import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Text, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class Job(Base):
    __tablename__ = "jobs"

    __table_args__ = (
        Index("ix_jobs_priority_created", "priority", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    type: Mapped[str] = mapped_column(String(64), default="custom", index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    assigned_worker: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)

    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    logs: Mapped[str | None] = mapped_column(Text, nullable=True)

    priority: Mapped[int] = mapped_column(Integer, default=2)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
