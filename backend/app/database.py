from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings

_engine = None
_async_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            connect_args={"check_same_thread": False},
        )
    return _engine


def get_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_factory


def reset_engine():
    global _engine, _async_session_factory
    if _engine:
        _engine.sync_engine.dispose()
    _engine = None
    _async_session_factory = None


engine = get_engine()
async_session_factory = get_session_factory()


class Base(DeclarativeBase):
    pass


async def get_db():
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    from .models.worker import Worker
    from .models.job import Job
    from .models.log import SystemLog
    from .models.user import User
    from .models.workflow import (
        Workflow, WorkflowTask, TaskDependency, WorkflowResult,
        Artifact, ExecutionMetric, CacheEntry, WorkflowEvent, WorkerCapability,
    )
    from .models.repository import (
        Repository, RepositoryFile, Symbol, SymbolImport, SymbolReference,
        DependencyEdge, CodeMetric, KnowledgeNode, KnowledgeEdge,
        RepositoryCache, RepositoryEvent,
    )
    from .models.ai import (
        AIModel, AISession, AIMessage, PromptTemplate, ToolDefinition,
        ToolCall, AIMemory, AIProviderConfig, RuntimeMetric,
    )
    from .models.agent import (
        Agent, AgentTask, AgentMessage, AgentReview, AgentMerge,
        AgentMemory, AgentMetric,
    )
    from .models.engineering import (
        EngineeringPlan, EngineeringTask, EngineeringPatch, EngineeringValidation,
        EngineeringRepair, EngineeringQuality, EngineeringApproval, EngineeringMetric,
        EngineeringReport,
    )
    from .models.studio import (
        StudioWorkspace, StudioProject, StudioLayout, StudioBookmark,
        StudioPreference, StudioHistory,
    )

    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
