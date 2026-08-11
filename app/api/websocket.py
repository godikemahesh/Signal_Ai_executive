"""
Signal — WebSocket Handler
Real-time WebSockets for live UI updates on signal events.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket client disconnected")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {e}")


ws_manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection endpoint for real-time updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for optional ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
