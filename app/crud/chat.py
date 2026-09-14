"""Chat session and message CRUD operations."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.enums import ChatRole


def get_session(db: Session, session_id: int) -> ChatSession | None:
    """Fetch a chat session by id."""
    return db.get(ChatSession, session_id)


def list_sessions(db: Session, user_id: int) -> list[ChatSession]:
    """List chat sessions for a user."""
    stmt = select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.id.desc())
    return list(db.execute(stmt).scalars().all())


def create_session(db: Session, user_id: int, title: str = "New chat") -> ChatSession:
    """Create a chat session."""
    session = ChatSession(user_id=user_id, title=title[:255])
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def add_message(
    db: Session,
    session_id: int,
    role: ChatRole,
    content: str,
    sources: list[dict[str, Any]] | None = None,
) -> ChatMessage:
    """Append a message to a session."""
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        sources=sources,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def list_messages(db: Session, session_id: int) -> list[ChatMessage]:
    """Return messages in chronological order."""
    stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id)
    return list(db.execute(stmt).scalars().all())
