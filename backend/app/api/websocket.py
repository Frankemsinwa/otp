import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from app.core.logging import get_logger

log = get_logger("api.websocket")
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        log.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        log.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_json(self, payload: dict):
        """Broadcast a JSON payload directly to all connected WebSocket clients."""
        message = json.dumps(payload)
        log.info(f"Broadcasting to {len(self.active_connections)} WebSocket client(s): type={payload.get('type')}")
        
        async with self._lock:
            connections = list(self.active_connections)
        
        disconnected = []
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                log.warning(f"WebSocket send failed: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            await self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for the Next.js frontend to receive live updates.
    The client doesn't need to send anything, just listen.
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as exc:
        log.warning("WebSocket dropped", extra={"error": str(exc)})
        await manager.disconnect(websocket)
