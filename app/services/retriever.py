"""Retrieve relevant knowledge chunks for a user query."""

from typing import Any
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.chat import SourceReference
from app.services.embedding import EmbeddingService, get_embedding_service
from app.services.vector_store import SearchHit, VectorStore, get_vector_store


class Retriever:
    """Embed a query and return top-k knowledge snippets from FAISS."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store = vector_store or get_vector_store()

    def retrieve(
        self,
        db: Session | None = None,
        query: str = "",
        top_k: int | None = None,
    ) -> list[SearchHit]:
        """Return ranked hits above the configured minimum similarity."""
        settings = get_settings()
        k = top_k or settings.RAG_TOP_K
        embedding = self.embedding_service.embed_query(query)
        hits = self.vector_store.search(db, embedding, top_k=k)
        return [hit for hit in hits if hit.score >= settings.RAG_MIN_SCORE]

    def retrieve_chunks(
        self,
        question: str,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Direct vector search returning chunk dictionaries."""
        embedding = self.embedding_service.embed_query(question)
        hits = self.vector_store.search_index(embedding, top_k=top_k)
        return hits

    def to_sources(self, hits: list[SearchHit]) -> list[SourceReference]:
        """Convert search hits into API source references."""
        sources: list[SourceReference] = []
        for hit in hits:
            filename = "unknown"
            if hasattr(hit, "document") and hit.document:
                filename = getattr(hit.document, "original_name", None) or getattr(hit.document, "filename", "unknown")
            elif hasattr(hit, "source"):
                filename = hit.source

            doc_id = getattr(hit.chunk, "document_id", None) if hasattr(hit, "chunk") else None
            chunk_idx = getattr(hit.chunk, "chunk_index", 0) if hasattr(hit, "chunk") else 0
            content = getattr(hit.chunk, "content", "") if hasattr(hit, "chunk") else getattr(hit, "content", "")
            excerpt = content[:300]
            score = round(float(hit.score), 4) if hasattr(hit, "score") else 0.0

            sources.append(
                SourceReference(
                    document=filename,
                    chunk=chunk_idx,
                    filename=filename,
                    chunk_index=chunk_idx,
                    document_id=doc_id,
                    score=score,
                    excerpt=excerpt,
                )
            )
        return sources
