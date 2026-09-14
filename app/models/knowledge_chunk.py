"""Embedded knowledge chunk ORM model."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import json_type


class KnowledgeChunk(Base):
    """Text chunk with metadata mapped to FAISS vectors."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", json_type(), nullable=True)
    extra: Mapped[Optional[dict[str, Any]]] = mapped_column(json_type(), nullable=True)
    embedding: Mapped[Optional[list[float]]] = mapped_column(json_type(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="chunks")

    @property
    def meta(self) -> dict[str, Any]:
        """Convenience accessor for chunk metadata."""
        return self.chunk_metadata or self.extra or {}
