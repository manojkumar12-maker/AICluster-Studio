import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

CC_DIR = Path(__file__).resolve().parent.parent.parent
WORKER_DIR = CC_DIR.parent / "worker"
WORKER_CONFIG_FILE = WORKER_DIR / "config.json"
WORKER_MAIN = WORKER_DIR / "scripts" / "run.py"
WORKER_VENV = WORKER_DIR / ".venv"

worker_process: asyncio.subprocess.Process | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Worker Control Center starting")
    yield
    global worker_process
    if worker_process and worker_process.returncode is None:
        worker_process.terminate()
        try:
            await asyncio.wait_for(worker_process.wait(), timeout=5)
        except asyncio.TimeoutError:
            worker_process.kill()
    logger.info("Worker Control Center stopped")


app = FastAPI(
    title="AICluster Worker Control Center",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .api.router import router
app.include_router(router, prefix="/api")
