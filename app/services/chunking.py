"""Simple deterministic text chunking for RAG indexing."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TextChunk:
    """A contiguous slice of a source document."""

    index: int
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    document_id: int | None = None

    @property
    def chunk_index(self) -> int:
        """Alias for index."""
        return self.index


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    document_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[TextChunk]:
    """Split text into overlapping chunks.

    Supports both character-based and paragraph-friendly slicing,
    preserving chunk index and metadata.
    """
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    meta = dict(metadata or {})
    chunks: list[TextChunk] = []
    start = 0
    text_length = len(cleaned)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        if end < text_length:
            boundary = cleaned.rfind(" ", start, end)
            if boundary > start + (chunk_size // 2):
                end = boundary

        content = cleaned[start:end].strip()
        if content:
            chunks.append(
                TextChunk(
                    index=len(chunks),
                    content=content,
                    metadata=dict(meta),
                    document_id=document_id,
                )
            )
        if end >= text_length:
            break

        next_start = max(start + 1, end - chunk_overlap)
        while next_start < text_length and cleaned[next_start] == " ":
            next_start += 1
        start = next_start

    if not chunks:
        chunks.append(
            TextChunk(
                index=0,
                content=cleaned,
                metadata=dict(meta),
                document_id=document_id,
            )
        )

    return chunks
