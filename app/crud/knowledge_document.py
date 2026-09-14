"""Knowledge document and chunk CRUD operations."""

from datetime import datetime, timezone
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.models.enums import DocumentStatus


def get_document(db: Session, document_id: int) -> KnowledgeDocument | None:
    """Fetch a knowledge document by id."""
    return db.get(KnowledgeDocument, document_id)


def list_documents(db: Session, skip: int = 0, limit: int = 50) -> list[KnowledgeDocument]:
    """Return a page of knowledge documents."""
    stmt = select(KnowledgeDocument).offset(skip).limit(limit).order_by(KnowledgeDocument.id.desc())
    return list(db.execute(stmt).scalars().all())


def create_document(
    db: Session,
    *,
    filename: str,
    original_name: str | None = None,
    file_type: str = "text",
    title: str | None = None,
    content_type: str = "text/plain",
    file_path: str,
    uploaded_by: int | None = None,
) -> KnowledgeDocument:
    """Persist metadata for an uploaded file."""
    document = KnowledgeDocument(
        filename=filename,
        original_name=original_name or filename,
        file_type=file_type,
        title=title or original_name or filename,
        content_type=content_type,
        file_path=file_path,
        uploaded_by=uploaded_by,
        status=DocumentStatus.UPLOADED,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def update_document_status(
    db: Session,
    document: KnowledgeDocument,
    status: DocumentStatus,
    chunk_count: int = 0,
    error_message: str | None = None,
) -> KnowledgeDocument:
    """Update indexing status for a document."""
    document.status = status
    document.chunk_count = chunk_count
    document.error_message = error_message
    if status in (DocumentStatus.PROCESSED, DocumentStatus.INDEXED):
        document.indexed_at = datetime.now(timezone.utc)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def replace_chunks(
    db: Session,
    document_id: int,
    chunks: list[KnowledgeChunk],
) -> None:
    """Replace all chunks for a document in a single transaction."""
    db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id))
    for chunk in chunks:
        db.add(chunk)
    db.commit()


def list_chunks_with_embeddings(db: Session) -> list[KnowledgeChunk]:
    """Return all chunks that have embeddings."""
    stmt = select(KnowledgeChunk).where(KnowledgeChunk.embedding.is_not(None))
    return list(db.execute(stmt).scalars().all())


def delete_document(db: Session, document: KnowledgeDocument) -> None:
    """Delete a document and its chunks."""
    db.delete(document)
    db.commit()
