import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    total_lines: Mapped[int] = mapped_column(Integer, default=0)
    total_symbols: Mapped[int] = mapped_column(Integer, default=0)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class RepositoryFile(Base):
    __tablename__ = "repository_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id"), index=True)
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    extension: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    lines: Mapped[int] = mapped_column(Integer, default=0)
    code_lines: Mapped[int] = mapped_column(Integer, default=0)
    comment_lines: Mapped[int] = mapped_column(Integer, default=0)
    blank_lines: Mapped[int] = mapped_column(Integer, default=0)
    hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_binary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    complexity: Mapped[float | None] = mapped_column(Float, nullable=True)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("ix_repo_file_path", "repository_id", "path", unique=True),)


class Symbol(Base):
    __tablename__ = "symbols"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id"), index=True)
    file_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_files.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    qualified_name: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    symbol_type: Mapped[str] = mapped_column(String(64), index=True)
    language: Mapped[str] = mapped_column(String(64), index=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_start: Mapped[int] = mapped_column(Integer, default=0)
    line_end: Mapped[int] = mapped_column(Integer, default=0)
    column_start: Mapped[int] = mapped_column(Integer, default=0)
    column_end: Mapped[int] = mapped_column(Integer, default=0)
    visibility: Mapped[str | None] = mapped_column(String(32), nullable=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    docstring: Mapped[str | None] = mapped_column(Text, nullable=True)
    complexity: Mapped[float | None] = mapped_column(Float, nullable=True)
    parameters: Mapped[dict] = mapped_column(JSON, default=list)
    decorators: Mapped[dict] = mapped_column(JSON, default=list)
    annotations: Mapped[dict] = mapped_column(JSON, default=dict)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_test: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("ix_symbol_qualified", "repository_id", "qualified_name"),)


class SymbolImport(Base):
    __tablename__ = "symbol_imports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id"), index=True)
    file_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_files.id"), index=True)
    source: Mapped[str] = mapped_column(String(512), nullable=False)
    imported_name: Mapped[str] = mapped_column(String(255), nullable=False)
    alias: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_relative: Mapped[bool] = mapped_column(Boolean, default=False)
    line: Mapped[int] = mapped_column(Integer, default=0)


class SymbolReference(Base):
    __tablename__ = "symbol_references"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id"), index=True)
    source_symbol_id: Mapped[str] = mapped_column(String(36), ForeignKey("symbols.id"), index=True)
    target_symbol_id: Mapped[str] = mapped_column(String(36), ForeignKey("symbols.id"), index=True)
    reference_type: Mapped[str] = mapped_column(String(64), default="call")
    file_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_files.id"), index=True)
    line: Mapped[int] = mapped_column(Integer, default=0)


class DependencyEdge(Base):
    __tablename__ = "dependency_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id"), index=True)
    source_file_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_files.id"), index=True)
    target_file_id: Mapped[str] = mapped_column(String(36), ForeignKey("repository_files.id"), index=True)
    dependency_type: Mapped[str] = mapped_column(String(64), default="import")
    weight: Mapped[int] = mapped_column(Integer, default=1)


class CodeMetric(Base):
    __tablename__ = "code_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id"), index=True)
    file_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("repository_files.id"), nullable=True, index=True)
    metric_type: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id"), index=True)
    node_type: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    qualified_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id"), index=True)
    source_node_id: Mapped[str] = mapped_column(String(36), ForeignKey("knowledge_nodes.id"), index=True)
    target_node_id: Mapped[str] = mapped_column(String(36), ForeignKey("knowledge_nodes.id"), index=True)
    edge_type: Mapped[str] = mapped_column(String(64), default="contains")
    weight: Mapped[float] = mapped_column(Float, default=1.0)


class RepositoryCache(Base):
    __tablename__ = "repository_cache"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id"), index=True)
    cache_key: Mapped[str] = mapped_column(String(256), index=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_repo_cache_key", "repository_id", "cache_key", unique=True),)


class RepositoryEvent(Base):
    __tablename__ = "repository_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
