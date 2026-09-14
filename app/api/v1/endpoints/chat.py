"""REST and WebSocket chat endpoints."""

from fastapi import APIRouter, Depends, WebSocket, WebSocketException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_from_token_param
from app.crud import chat as chat_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ChatMessageRead, ChatRequest, ChatResponse, ChatSessionRead
from app.services.chat_service import ChatService
from app.websocket.chat_handler import handle_chat_socket

router = APIRouter()


@router.post("", response_model=ChatResponse, summary="Ask the hospital knowledge assistant")
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Answer a question using RAG (retrieval + Groq or retrieval-only)."""
    return ChatService().reply(db, current_user, payload)


@router.get("/sessions", response_model=list[ChatSessionRead], summary="List my chat sessions")
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the caller's chat sessions."""
    return chat_crud.list_sessions(db, current_user.id)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageRead],
    summary="List messages in a session",
)
def list_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return transcript messages for a session owned by the caller."""
    session = chat_crud.get_session(db, session_id)
    if session is None or session.user_id != current_user.id:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return chat_crud.list_messages(db, session_id)


@router.websocket("/ws")
async def chat_ws(
    websocket: WebSocket,
    token: str | None = None,
    db: Session = Depends(get_db),
) -> None:
    """Realtime chat with status events. Pass JWT as `?token=`."""
    try:
        user = get_current_user_from_token_param(token=token, authorization=None, db=db)
    except Exception as exc:  # noqa: BLE001
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc
    await handle_chat_socket(websocket, db, user)
