"""Chat and RAG schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ChatRole


class SourceReference(BaseModel):
    """A retrieved chunk cited in an answer."""

    document: str = "unknown"
    chunk: int = 0
    filename: str | None = None
    chunk_index: int | None = None
    document_id: int | None = None
    score: float = 0.0
    excerpt: str = ""

    @model_validator(mode="before")
    @classmethod
    def pre_sync(cls, data: Any) -> Any:
        if isinstance(data, dict):
            doc = data.get("document") or data.get("filename") or "unknown"
            chk = data.get("chunk")
            if chk is None:
                chk = data.get("chunk_index", 0)
            data["document"] = doc
            data["filename"] = data.get("filename") or doc
            data["chunk"] = chk
            data["chunk_index"] = data.get("chunk_index") if data.get("chunk_index") is not None else chk
        return data


class ChatRequest(BaseModel):
    """REST chat request."""

    question: str | None = None
    message: str | None = None
    session_id: int | None = None
    mode: Literal["groq", "retrieval_only"] | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)

    @model_validator(mode="after")
    def sync_query(self) -> "ChatRequest":
        text = (self.question or self.message or "").strip()
        if not text:
            raise ValueError("question or message is required")
        self.question = text
        self.message = text
        return self


class ChatResponse(BaseModel):
    """Grounded chatbot answer."""

    answer: str
    sources: list[SourceReference] = []
    session_id: int | None = None
    emergency: bool = False
    mode: str = "retrieval_only"
    retrieved: int = 0


class ChatSessionRead(BaseModel):
    """Chat session metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    created_at: datetime | None = None


class ChatMessageRead(BaseModel):
    """Stored chat message."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: ChatRole
    content: str
    sources: list[dict[str, Any]] | None
    created_at: datetime | None = None
