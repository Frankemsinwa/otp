import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("api.websocket")
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.redis: Redis | None = None
        self.pubsub = None
        self.channel_name = "otp_live_feed"
        self._listener_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def connect_redis(self):
        """Initialize Redis connection and start pub/sub listener."""
        async with self._lock:
            if not self.redis:
                self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
                self.pubsub = self.redis.pubsub()
                await self.pubsub.subscribe(self.channel_name)
                self._listener_task = asyncio.create_task(self._listen_to_redis())
                log.info("WebSocket Manager connected to Redis pub/sub")

    async def disconnect_redis(self):
        """Cleanup Redis connection."""
        if self._listener_task:
            self._listener_task.cancel()
        if self.pubsub:
            await self.pubsub.unsubscribe(self.channel_name)
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()

    async def _listen_to_redis(self):
        """Background task that reads from Redis and broadcasts to all WebSockets."""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    await self._broadcast_to_clients(data)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            log.error("Redis listener error", extra={"error": str(exc)})

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        log.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            log.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_json(self, payload: dict):
        """Publish a JSON payload to the Redis channel (called by other services like scheduler)."""
        if not self.redis:
            await self.connect_redis()
        
        message = json.dumps(payload)
        await self.redis.publish(self.channel_name, message)

    async def _broadcast_to_clients(self, message: str):
        """Send a string message to all connected local WebSocket clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)


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
            # We wait for messages from the client (e.g. ping/pong keepalive)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        log.warning("WebSocket dropped", extra={"error": str(exc)})
        manager.disconnect(websocket)
