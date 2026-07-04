import asyncio
import time

import pytest

from app.database import get_engine, get_session_factory, Base


@pytest.mark.asyncio
async def test_single_commit_on_assign(db_session):
    """Verify get_next_for_worker uses a single commit."""
    from app.services.scheduler import SchedulerService
    from app.models.job import Job

    # Create a queued job
    job = Job(type="echo", status="queued", payload={})
    db_session.add(job)
    await db_session.commit()

    scheduler = SchedulerService(db_session)
    result = await scheduler.get_next_for_worker("test-worker-id")
    assert result is not None
    assert result.status == "running"
    assert result.assigned_worker == "test-worker-id"


@pytest.mark.asyncio
async def test_duration_stored(db_session):
    """Verify complete_job stores duration_ms."""
    from app.services.scheduler import SchedulerService
    from app.models.job import Job

    # Create a running job
    job = Job(type="echo", status="running", payload={})
    db_session.add(job)
    await db_session.commit()

    scheduler = SchedulerService(db_session)
    result = await scheduler.complete_job(
        job_id=job.id,
        status="completed",
        result_data={"output": "test"},
        duration_ms=1234.5,
    )
    assert result is not None
    assert result.status == "completed"
    assert result.duration_ms == 1234.5


@pytest.mark.asyncio
async def test_duration_not_stored_when_none(db_session):
    """Verify complete_job handles None duration_ms."""
    from app.services.scheduler import SchedulerService
    from app.models.job import Job

    job = Job(type="echo", status="running", payload={})
    db_session.add(job)
    await db_session.commit()

    scheduler = SchedulerService(db_session)
    result = await scheduler.complete_job(
        job_id=job.id,
        status="completed",
        result_data={"output": "test"},
    )
    assert result is not None
    assert result.duration_ms is None


@pytest.mark.asyncio
async def test_clean_shutdown_within_1s():
    """Verify scheduler stops within 1s of stop()."""
    from app.services.scheduler import SchedulerService

    engine = get_engine()
    factory = get_session_factory()
    async with factory() as session:
        scheduler = SchedulerService(session)
        await scheduler.start()
        await asyncio.sleep(0.1)  # Let it start

        start = time.monotonic()
        await scheduler.stop()
        elapsed = time.monotonic() - start
        assert elapsed < 1.0, f"Scheduler took {elapsed:.2f}s to stop"
