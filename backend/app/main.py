import asyncio
import logging
from contextlib import asynccontextmanager

from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db, get_db
from .api.v1 import router as api_router
from .api.dependencies import auth_middleware
from .middleware import limiter, SlowAPIMiddleware
from .websocket.manager import ws_manager
from .services.worker_manager import WorkerManagerService
from .services.auth import AuthService
from .services.scheduler import SchedulerService
from .logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

offline_checker_task = None
scheduler_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global offline_checker_task
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    await init_db()
    logger.info("Database initialized")

    async for db in get_db():
        auth_service = AuthService(db)
        admin_password = await auth_service.seed_default_admin()
        if admin_password:
            print(f"ADMIN PASSWORD: {admin_password}", file=__import__('sys').stderr)
        break

    async def check_offline_workers():
        while True:
            try:
                async for db in get_db():
                    manager = WorkerManagerService(db)
                    marked = await manager.mark_offline_workers()
                    if marked:
                        logger.info(f"Marked {marked} workers offline")
                    break
            except Exception as e:
                logger.error(f"Offline checker error: {e}")
            await asyncio.sleep(10)

    offline_checker_task = asyncio.create_task(check_offline_workers())
    logger.info("Offline worker checker started")

    async def run_scheduler():
        while True:
            try:
                async for db in get_db():
                    scheduler = SchedulerService(db)
                    await scheduler._process_queue()
                    break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(2)

    scheduler_task = asyncio.create_task(run_scheduler())
    logger.info("Job scheduler started")

    yield

    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
    if offline_checker_task:
        offline_checker_task.cancel()
        try:
            await offline_checker_task
        except asyncio.CancelledError:
            pass
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(auth_middleware)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.include_router(api_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    await ws_manager.connect(websocket, token=token)
    if websocket not in ws_manager.active_connections:
        return
    try:
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text('{"type":"pong"}')
            except WebSocketDisconnect:
                break
    except Exception:
        pass
    finally:
        ws_manager.disconnect(websocket)


@app.get("/")
async def root():
    return FileResponse(Path(__file__).parent / "static" / "dashboard.html")
