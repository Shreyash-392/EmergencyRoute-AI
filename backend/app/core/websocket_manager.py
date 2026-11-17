from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages active WebSocket connections for real-time telemetry, closures,
    and emergency dispatch updates with an in-memory fallback polling buffer.
    """

    def __init__(self, max_buffer_size: int = 100):
        self.active_connections: Set[WebSocket] = set()
        self.max_buffer_size = max_buffer_size
        self._event_buffer: List[Dict[str, Any]] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Any):
        """Broadcasts structured event to all connected WebSocket clients."""
        payload = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        # Save to buffer for polling fallback
        self._event_buffer.append(payload)
        if len(self._event_buffer) > self.max_buffer_size:
            self._event_buffer.pop(0)

        # Broadcast to active sockets
        dead_connections = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(payload)
            except Exception as e:
                logger.warning(f"Error sending message to WebSocket client: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns recent broadcast events for clients using the HTTP polling fallback."""
        return self._event_buffer[-limit:]


websocket_manager = WebSocketManager()

