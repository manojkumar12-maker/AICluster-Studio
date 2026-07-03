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
from .websocket.manager import ws_manager
from .services.worker_manager import WorkerManagerService
from .services.auth import AuthService
from .logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

offline_checker_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global offline_checker_task
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    await init_db()
    logger.info("Database initialized")

    async for db in get_db():
        auth_service = AuthService(db)
        await auth_service.seed_default_admin()
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

    yield

    if offline_checker_task:
        offline_checker_task.cancel()
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

app.include_router(api_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
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
