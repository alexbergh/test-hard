"""WebSocket endpoint for real-time scan notifications."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/scans")
async def scan_notifications(websocket: WebSocket):
    """WebSocket endpoint for receiving scan status updates.

    Messages are JSON objects with fields:
      - type: "scan_started" | "scan_completed" | "scan_failed"
      - scan_id: int
      - scanner: str (optional)
      - host_name: str (optional)
      - score: int (optional, on completion)
      - error: str (optional, on failure)
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; client can send ping/pong
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
