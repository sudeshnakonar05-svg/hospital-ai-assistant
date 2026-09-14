"""Ingest sample knowledge documents into PostgreSQL and FAISS vector index."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from uuid import uuid4

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.crud import knowledge_document as document_crud
from app.crud.user import get_by_email, create_superuser
from app.db.session import SessionLocal
from app.services.rag_service import RagIndexer, save_upload

KB_DIR = ROOT / "sample_data" / "knowledge"
ALT_KB_DIR = ROOT / "data" / "knowledge_base"


def main() -> None:
    """Upload, chunk, embed, and index every knowledge document into FAISS."""
    configure_logging()
    settings = get_settings()

    # Determine knowledge documents source
    files_to_process: list[Path] = []
    if KB_DIR.exists():
        files_to_process.extend(
            [p for p in KB_DIR.iterdir() if p.suffix.lower() in settings.ALLOWED_EXTENSIONS]
        )
    if ALT_KB_DIR.exists():
        for p in ALT_KB_DIR.iterdir():
            if p.suffix.lower() in settings.ALLOWED_EXTENSIONS and p.name not in [f.name for f in files_to_process]:
                files_to_process.append(p)

    if not files_to_process:
        print("No documents found to ingest.")
        return

    db = SessionLocal()
    total_docs = 0
    total_chunks = 0

    try:
        admin_email = settings.effective_admin_email
        admin_pass = settings.effective_admin_password
        admin = get_by_email(db, admin_email)
        if admin is None:
            admin = create_superuser(
                db,
                email=admin_email,
                password=admin_pass,
                full_name=settings.effective_admin_full_name,
            )

        indexer = RagIndexer()

        for path in sorted(files_to_process):
            stored = Path(settings.UPLOAD_DIR) / f"{uuid4().hex}{path.suffix.lower()}"
            save_upload(path.read_bytes(), stored)
            file_type = path.suffix.lower().lstrip(".") or "text"

            document = document_crud.create_document(
                db,
                filename=stored.name,
                original_name=path.name,
                file_type=file_type,
                title=path.stem.replace("_", " ").title(),
                content_type="text/plain",
                file_path=str(stored),
                uploaded_by=admin.id,
            )
            indexed = indexer.index_document(db, document)
            total_docs += 1
            total_chunks += indexed.chunk_count

        print(f"Documents processed: {total_docs}")
        print(f"Chunks created: {total_chunks}")
        print("Vector index updated successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
