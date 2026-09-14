"""Chat orchestration: guards, retrieval, LLM, persistence."""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.crud import chat as chat_crud
from app.llm.factory import get_llm
from app.models.enums import ChatRole
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.emergency_guard import emergency_response, is_emergency
from app.services.medical_guard import apply_medical_guard
from app.services.retriever import Retriever


class ChatService:
    """Handle a user chat turn against the hospital knowledge base."""

    def __init__(self, retriever: Retriever | None = None) -> None:
        self.retriever = retriever or Retriever()

    def reply(self, db: Session, user: User, payload: ChatRequest) -> ChatResponse:
        """Produce a grounded answer and optionally persist transcript."""
        settings = get_settings()
        query_text = payload.question or payload.message or ""
        session = None

        if hasattr(user, "id"):
            if payload.session_id:
                session = chat_crud.get_session(db, payload.session_id)
                if session is None or session.user_id != user.id:
                    from app.core.exceptions import AppError
                    raise AppError(404, "Chat session not found", "session_not_found")
            if session is None:
                title = query_text[:80]
                session = chat_crud.create_session(db, user.id, title=title)
            chat_crud.add_message(db, session.id, ChatRole.USER, query_text)

        mode = payload.mode or settings.LLM_PROVIDER

        if is_emergency(query_text):
            answer = emergency_response()
            if session:
                chat_crud.add_message(db, session.id, ChatRole.ASSISTANT, answer, sources=[])
            return ChatResponse(
                session_id=session.id if session else None,
                answer=answer,
                sources=[],
                emergency=True,
                mode=mode,
                retrieved=0,
            )

        hits = self.retriever.retrieve(db, query_text, top_k=payload.top_k)
        sources = self.retriever.to_sources(hits)
        llm = get_llm(mode)
        raw_answer = llm.generate(query_text, sources)
        answer = apply_medical_guard(raw_answer, emergency=False)

        if session:
            source_dicts = [source.model_dump() for source in sources]
            chat_crud.add_message(db, session.id, ChatRole.ASSISTANT, answer, sources=source_dicts)

        return ChatResponse(
            session_id=session.id if session else None,
            answer=answer,
            sources=sources,
            emergency=False,
            mode=llm.name,
            retrieved=len(sources),
        )
