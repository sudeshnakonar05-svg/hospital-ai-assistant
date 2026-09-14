"""Knowledge document schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentStatus


class DocumentRead(BaseModel):
    """Uploaded knowledge document metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str = "text"
    file_path: str | None = None
    title: str | None = None
    original_name: str | None = None
    content_type: str | None = None
    uploaded_by: int | None = None
    status: DocumentStatus
    error_message: str | None = None
    chunk_count: int = 0
    extra: dict[str, Any] | None = None
    created_at: datetime | None = None
    indexed_at: datetime | None = None


class IndexRequest(BaseModel):
    """Optional re-index flags."""

    force: bool = False


class SearchRequest(BaseModel):
    """Vector search query."""

    query: str = Field(min_length=2, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
