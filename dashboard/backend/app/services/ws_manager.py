"""WebSocket connection manager for real-time notifications."""

import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections for scan notifications."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected, total: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected, total: %d", len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]):
        """Send a JSON message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.active_connections.remove(conn)

    async def send_scan_event(self, event_type: str, scan_id: int, **kwargs):
        """Broadcast a scan lifecycle event."""
        message = {
            "type": event_type,
            "scan_id": scan_id,
            **kwargs,
        }
        await message_queue.put(message)


# Singleton instance
ws_manager = ConnectionManager()

# Async queue for cross-task communication (scan tasks -> WS broadcast)
import asyncio

message_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
