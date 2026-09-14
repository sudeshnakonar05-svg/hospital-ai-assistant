"""WebSocket chat protocol handler."""

import logging

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService
from app.services.emergency_guard import is_emergency
from app.websocket.manager import manager

logger = logging.getLogger(__name__)


async def handle_chat_socket(websocket: WebSocket, db: Session, user: User) -> None:
    """Accept messages and stream status events then a final answer."""
    await manager.connect(user.id, websocket)
    await manager.send_json(
        websocket,
        {"event": "ready", "message": "Connected to hospital assistant", "user_id": user.id},
    )
    chat_service = ChatService()
    try:
        while True:
            payload = await websocket.receive_json()
            message = str(payload.get("message", "")).strip()
            if not message:
                await manager.send_json(
                    websocket, {"event": "error", "detail": "message is required"}
                )
                continue
            await manager.send_json(websocket, {"event": "status", "message": "Checking safety..."})
            if not is_emergency(message):
                await manager.send_json(
                    websocket, {"event": "status", "message": "Retrieving knowledge..."}
                )
            request = ChatRequest(
                message=message,
                session_id=payload.get("session_id"),
                mode=payload.get("mode"),
                top_k=payload.get("top_k"),
            )
            response = chat_service.reply(db, user, request)
            await manager.send_json(
                websocket,
                {
                    "event": "answer",
                    "session_id": response.session_id,
                    "answer": response.answer,
                    "sources": [source.model_dump() for source in response.sources],
                    "emergency": response.emergency,
                    "mode": response.mode,
                    "retrieved": response.retrieved,
                },
            )
    except WebSocketDisconnect:
        manager.disconnect(user.id, websocket)
    except Exception:  # noqa: BLE001
        logger.exception("WebSocket chat failed")
        try:
            await manager.send_json(
                websocket, {"event": "error", "detail": "Chat processing failed"}
            )
        finally:
            manager.disconnect(user.id, websocket)
