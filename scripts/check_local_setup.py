"""Validate local environment setup for the Hospital AI Assistant."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text

from app.core.config import get_settings


def main() -> None:
    """Validate that required configuration, directories, and database are usable."""
    settings = get_settings()
    print("=" * 60)
    print(f"Project: {settings.APP_NAME}")
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Environment: {settings.APP_ENV}")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"JWT Secret Configured: {len(settings.JWT_SECRET_KEY) >= 16}")
    print(f"RAG Default TOP_K: {settings.RAG_TOP_K}")
    print(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"LLM Provider: {settings.LLM_PROVIDER} (Default: retrieval_only)")
    print(f"Groq API Key Provided: {bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith('your_'))}")

    # Check directories and vector store
    upload_path = Path(settings.UPLOAD_DIR)
    index_path = Path(settings.VECTOR_INDEX_PATH)
    meta_path = Path(settings.VECTOR_METADATA_PATH)
    sample_kb = ROOT / "sample_data" / "knowledge"

    print(f"Upload Directory: {upload_path} (Exists: {upload_path.exists()})")
    print(f"Sample Knowledge Base: {sample_kb} (Files: {len(list(sample_kb.glob('*.*'))) if sample_kb.exists() else 0})")
    print(f"FAISS Index Path: {index_path} (Exists: {index_path.exists()})")
    print(f"Vector Metadata Path: {meta_path} (Exists: {meta_path.exists()})")

    # Check FAISS library
    try:
        import faiss
        print(f"FAISS Library: Available (v{getattr(faiss, '__version__', 'installed')})")
    except ImportError:
        print("FAISS Library: NOT INSTALLED (run: pip install faiss-cpu)")

    # Check Database Connection
    try:
        from app.db.session import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            dialect = conn.dialect.name
            print(f"Database Reachable: YES ({dialect})")
    except Exception as exc:
        print(f"Database Reachable: NO ({exc})")

    print("=" * 60)


if __name__ == "__main__":
    main()
