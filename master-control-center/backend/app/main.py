import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent / "backend"
DATA_FILE = BACKEND_DIR / "data" / "aicluster.db"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Master Control Center starting")
    yield
    logger.info("Master Control Center stopped")


app = FastAPI(
    title="AICluster Master Control Center",
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
