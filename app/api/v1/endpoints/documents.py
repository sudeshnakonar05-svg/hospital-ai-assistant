"""Knowledge document upload, indexing, and search endpoints."""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import StaffUser, get_current_user
from app.core.config import get_settings
from app.crud import knowledge_document as document_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import SourceReference
from app.schemas.document import DocumentRead, SearchRequest
from app.services.rag_service import RagIndexer, save_upload
from app.services.retriever import Retriever
from app.services.vector_store import get_vector_store

router = APIRouter()


@router.get("", response_model=list[DocumentRead], summary="List knowledge documents")
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List uploaded knowledge files."""
    return document_crud.list_documents(db, skip=skip, limit=limit)


@router.post(
    "/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a knowledge file (staff/admin)",
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(StaffUser),
):
    """Validate, store, and index a PDF/DOCX/TXT/Markdown file."""
    settings = get_settings()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported type. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(contents) > settings.UPLOAD_MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    stored_name = f"{uuid4().hex}{suffix}"
    destination = Path(settings.UPLOAD_DIR) / stored_name
    save_upload(contents, destination)
    document = document_crud.create_document(
        db,
        filename=stored_name,
        original_name=file.filename or stored_name,
        content_type=file.content_type or "application/octet-stream",
        file_path=str(destination),
        uploaded_by=current_user.id,
    )
    indexer = RagIndexer()
    return indexer.index_document(db, document)


@router.post("/{document_id}/index", response_model=DocumentRead, summary="Re-index a document")
def reindex_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(StaffUser),
):
    """Re-run chunking and embedding for a stored file."""
    document = document_crud.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return RagIndexer().index_document(db, document)


@router.post("/search", response_model=list[SourceReference], summary="Search indexed knowledge")
def search_documents(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Vector search over indexed chunks using RAG_TOP_K or an explicit top_k."""
    retriever = Retriever()
    hits = retriever.retrieve(db, payload.query, top_k=payload.top_k)
    return retriever.to_sources(hits)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a document")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(StaffUser),
) -> None:
    """Delete a knowledge document and its chunks."""
    document = document_crud.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    path = Path(document.file_path)
    document_crud.delete_document(db, document)
    vector_store = get_vector_store()
    vector_store.remove_document_vectors(document_id)
    vector_store.save_index()
    if path.exists():
        path.unlink()
