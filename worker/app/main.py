import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings
from .core.state import WorkerState
from .core.constants import VERSION, POLL_INTERVAL, PROGRESS_INTERVAL, PROGRESS_PERCENT_THRESHOLD
from .logging.setup import setup_worker_logging
from .utils.http_client import WorkerHttpClient
from .utils.retry import RetryHandler
from .services.registrar import Registrar
from .services.heartbeat import HeartbeatService
from .services.poller import JobPoller
from .services.reporter import Reporter
from .executor.registry import JobRegistry
from .executor.handlers.echo import EchoJobHandler
from .executor.handlers.sleep import SleepJobHandler
from .executor.handlers.dir_scan import DirectoryScanHandler
from .executor.handlers.hash_file import HashFileHandler
from .executor.handlers.count_files import CountFilesHandler

setup_worker_logging(log_level=settings.log_level)
logger = logging.getLogger(__name__)

state = WorkerState.STARTING
http_client: WorkerHttpClient | None = None
registrar: Registrar | None = None
heartbeat_service: HeartbeatService | None = None
poller: JobPoller | None = None
reporter: Reporter | None = None
job_registry = JobRegistry()
shutdown_event = asyncio.Event()


class _NoOpReporter:
    async def report_progress(self, job_id=None, progress=None, logs=None):
        pass
    async def report_result(self, job_id=None, status=None, result=None, error=None, duration_ms=None, logs=None):
        pass

_noop_reporter = _NoOpReporter()

job_registry.register("echo", EchoJobHandler())
job_registry.register("sleep", SleepJobHandler())
job_registry.register("dir_scan", DirectoryScanHandler())
job_registry.register("hash_file", HashFileHandler())
job_registry.register("count_files", CountFilesHandler())


@asynccontextmanager
async def lifespan(app: FastAPI):
    global state
    asyncio.create_task(_run_worker())
    yield
    state = WorkerState.SHUTDOWN
    shutdown_event.set()
    await _cleanup()


app = FastAPI(
    title="AICluster Worker",
    version=VERSION,
    lifespan=lifespan,
)


async def _run_worker():
    global state, http_client, registrar, heartbeat_service, poller, reporter

    state = WorkerState.LOADING_CONFIG
    logger.info(f"Starting worker: {settings.get_worker_name()} (v{VERSION})")

    state = WorkerState.CONNECTING
    reporter = _noop_reporter  # type: ignore
    http_client = WorkerHttpClient(settings.master_url, worker_secret=settings.worker_secret)
    registrar = Registrar(http_client)
    retry = RetryHandler()

    while state not in (WorkerState.SHUTDOWN, WorkerState.EXIT):
        state = WorkerState.REGISTERING
        worker_id = await registrar.register()

        if worker_id is None:
            state = WorkerState.RETRY
            logger.warning("Registration failed, retrying...")
            await retry.wait()
            continue

        retry.reset()
        state = WorkerState.ONLINE

        heartbeat_service = HeartbeatService(worker_id, http_client)
        poller = JobPoller(worker_id, http_client)
        reporter = Reporter(worker_id, http_client)
        await heartbeat_service.start()
        await poller.start()

        await _worker_loop(worker_id)

    state = WorkerState.EXIT


async def _worker_loop(worker_id: str):
    global state

    while state not in (WorkerState.SHUTDOWN, WorkerState.EXIT):
        state = WorkerState.HEARTBEAT
        await asyncio.sleep(settings.heartbeat_interval)

        state = WorkerState.POLL_JOB
        job_data = await poller.poll()

        if not isinstance(job_data, dict):
            state = WorkerState.NO_JOB
            await asyncio.sleep(settings.poll_interval)
            continue

        if not job_data.get("id"):
            state = WorkerState.NO_JOB
            await asyncio.sleep(settings.poll_interval)
            continue

        state = WorkerState.HAS_JOB
        await _execute_job(worker_id, job_data)


async def _execute_job(worker_id: str, job_data: dict):
    global state
    job_id = job_data.get("id", "unknown")
    job_type = job_data.get("type", "custom")
    payload = job_data.get("payload", {})
    start_time = asyncio.get_event_loop().time()

    logger.info(
        f"Executing job {job_id} (type: {job_type})",
        extra={"worker_id": worker_id, "job_id": job_id},
    )

    handler = job_registry.get_handler(job_type)
    if handler is None:
        await reporter.report_result(job_id, "failed", error=f"Unknown job type: {job_type}")
        return

    state = WorkerState.EXECUTING

    try:
        result = await handler.execute(job_id, payload)

        duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        await reporter.report_progress(job_id, 100.0)
        await reporter.report_result(job_id, "completed", result=result, duration_ms=duration_ms)

        logger.info(
            f"Job {job_id} completed in {duration_ms:.0f}ms",
            extra={"worker_id": worker_id, "job_id": job_id},
        )

    except asyncio.CancelledError:
        duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        await reporter.report_result(job_id, "cancelled", duration_ms=duration_ms)
    except Exception as e:
        duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        error_msg = str(e)
        logger.error(
            f"Job {job_id} failed: {error_msg}",
            extra={"worker_id": worker_id, "job_id": job_id},
        )
        await reporter.report_result(job_id, "failed", error=error_msg, duration_ms=duration_ms)


def _should_report_progress(
    current: float, last_reported: float, last_report_time: float
) -> bool:
    now = asyncio.get_event_loop().time()
    if current - last_reported >= PROGRESS_PERCENT_THRESHOLD:
        return True
    if now - last_report_time >= PROGRESS_INTERVAL:
        return True
    return False


async def _cleanup():
    if heartbeat_service:
        await heartbeat_service.stop()
    if http_client:
        await http_client.close()
    logger.info("Worker shutdown complete")


def _signal_handler(sig, frame):
    global state
    logger.info(f"Received signal {sig}, shutting down...")
    state = WorkerState.SHUTDOWN
    shutdown_event.set()


def run():
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.worker_host,
        port=settings.worker_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
