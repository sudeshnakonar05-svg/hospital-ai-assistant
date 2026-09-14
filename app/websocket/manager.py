"""In-memory WebSocket connection manager."""

import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Track active WebSocket clients by user id."""

    def __init__(self) -> None:
        self._connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Accept and register a websocket."""
        await websocket.accept()
        self._connections[user_id].append(websocket)
        logger.info("WebSocket connected for user %s", user_id)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """Remove a websocket from the registry."""
        connections = self._connections.get(user_id, [])
        if websocket in connections:
            connections.remove(websocket)
        logger.info("WebSocket disconnected for user %s", user_id)

    async def send_json(self, websocket: WebSocket, payload: dict) -> None:
        """Send a JSON event to one client."""
        await websocket.send_json(payload)


manager = ConnectionManager()
