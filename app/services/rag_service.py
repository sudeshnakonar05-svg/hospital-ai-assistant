"""RAG pipeline orchestration and document indexing into FAISS."""

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.crud import knowledge_document as document_crud
from app.models.enums import DocumentStatus
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.services.chunking import chunk_text
from app.services.document_loader import extract_text
from app.services.embedding import EmbeddingService, get_embedding_service
from app.services.vector_store import VectorStore, get_vector_store

logger = logging.getLogger(__name__)


class RagIndexer:
    """Load, chunk, embed, and persist a knowledge document into PostgreSQL and FAISS."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store = vector_store or get_vector_store()

    def index_document(self, db: Session, document: KnowledgeDocument) -> KnowledgeDocument:
        """Run the full indexing pipeline for one document."""
        settings = get_settings()
        document_crud.update_document_status(db, document, DocumentStatus.PROCESSING)
        try:
            text = extract_text(document.file_path)
            chunks = chunk_text(
                text,
                chunk_size=settings.RAG_CHUNK_SIZE,
                chunk_overlap=settings.RAG_CHUNK_OVERLAP,
                document_id=document.id,
                metadata={"source": document.original_name or document.filename},
            )
            if not chunks:
                raise ValueError("No text chunks produced from document")

            contents = [chunk.content for chunk in chunks]
            embeddings = self.embedding_service.embed(contents)

            # Build database chunk records
            records = [
                KnowledgeChunk(
                    document_id=document.id,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    chunk_metadata={"source": document.original_name or document.filename, "chunk": chunk.index},
                    extra={"source": document.original_name or document.filename},
                    embedding=vector,
                )
                for chunk, vector in zip(chunks, embeddings, strict=True)
            ]
            document_crud.replace_chunks(db, document.id, records)

            # Add to FAISS vector store
            faiss_metas = [
                {
                    "document_id": document.id,
                    "document": document.original_name or document.filename,
                    "source": document.original_name or document.filename,
                    "chunk": chunk.index,
                    "chunk_index": chunk.index,
                    "content": chunk.content,
                }
                for chunk in chunks
            ]
            self.vector_store.replace_document_vectors(embeddings, faiss_metas, document.id)
            self.vector_store.save_index()

            updated = document_crud.update_document_status(
                db, document, DocumentStatus.INDEXED, chunk_count=len(records)
            )
            logger.info("Indexed document %s into %s chunks with FAISS", document.id, len(records))
            return updated
        except Exception as exc:
            logger.exception("Failed to index document %s", document.id)
            return document_crud.update_document_status(
                db,
                document,
                DocumentStatus.FAILED,
                error_message=str(exc),
            )


def save_upload(contents: bytes, destination: Path) -> None:
    """Write uploaded bytes to disk."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(contents)
