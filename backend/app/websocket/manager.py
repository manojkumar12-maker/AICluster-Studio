import json
import logging
from typing import Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self, max_connections: int = 100):
        self.active_connections: Set[WebSocket] = set()
        self.max_connections = max_connections

    async def connect(self, websocket: WebSocket):
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(code=1013, reason="Too many connections")
            logger.warning(f"WebSocket rejected: max connections ({self.max_connections}) reached")
            return
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected ({len(self.active_connections)} total)")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected ({len(self.active_connections)} total)")

    async def broadcast(self, event_type: str, data: dict):
        if not self.active_connections:
            return
        message = json.dumps({"type": event_type, "data": data}, default=str)
        dead: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.active_connections.discard(d)

    async def broadcast_worker_update(self, worker: dict):
        await self.broadcast("worker_update", worker)

    async def broadcast_job_update(self, job: dict):
        await self.broadcast("job_update", job)

    async def broadcast_dashboard(self, dashboard: dict):
        await self.broadcast("dashboard", dashboard)


ws_manager = WebSocketManager()
