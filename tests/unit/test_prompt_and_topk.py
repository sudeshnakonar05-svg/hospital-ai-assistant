"""Unit tests for RAG prompts and retrieval top-k."""

from app.core.config import get_settings
from app.schemas.chat import SourceReference
from app.services.prompt_builder import SYSTEM_PROMPT, build_rag_prompt, build_retrieval_answer
from app.services.vector_store import VectorStore


def test_settings_expose_postgres_jwt_and_topk() -> None:
    """Required runtime knobs are present on Settings."""
    settings = get_settings()
    assert settings.DATABASE_URL
    assert len(settings.JWT_SECRET_KEY) >= 16
    assert settings.RAG_TOP_K >= 1


def test_rag_prompt_includes_sources_and_safety() -> None:
    """The Groq prompt is grounded in retrieved excerpts."""
    sources = [
        SourceReference(
            document_id=1,
            filename="visiting_hours.md",
            chunk_index=0,
            score=0.91,
            excerpt="ICU visiting is 11:00 AM to 1:00 PM.",
        )
    ]
    messages = build_rag_prompt("When can I visit ICU?", sources)
    assert messages[0]["role"] == "system"
    assert "diagnosis" in SYSTEM_PROMPT.lower() or "diagnos" in messages[0]["content"].lower()
    assert "visiting_hours.md" in messages[1]["content"]
    assert "When can I visit ICU?" in messages[1]["content"]


def test_retrieval_only_answer_lists_filenames() -> None:
    """Extractive mode cites source files."""
    sources = [
        SourceReference(
            document_id=2,
            filename="appointment_policy.md",
            chunk_index=0,
            score=0.8,
            excerpt="Appointments should be scheduled at least 24 hours in advance.",
        )
    ]
    answer = build_retrieval_answer("How early should I book?", sources)
    assert "appointment_policy.md" in answer
    assert "24 hours" in answer


def test_empty_retrieval_explains_missing_knowledge() -> None:
    """No hits produce a clear fallback."""
    answer = build_retrieval_answer("unknown topic", [])
    assert "knowledge base" in answer.lower()


def test_vector_store_respects_top_k(db) -> None:
    """Python fallback search returns at most top_k hits."""
    from app.crud.knowledge_document import create_document, replace_chunks
    from app.crud.user import create_superuser
    from app.models.knowledge_chunk import KnowledgeChunk

    admin = create_superuser(db, "admin@hospital.com", "ChangeMeAdmin123!", "Admin")
    document = create_document(
        db,
        filename="a.txt",
        original_name="a.txt",
        content_type="text/plain",
        file_path="a.txt",
        uploaded_by=admin.id,
    )
    chunks = [
        KnowledgeChunk(
            document_id=document.id,
            chunk_index=index,
            content=f"token-{index} hospital policy",
            embedding=[float(index + 1)] + [0.0] * 383,
        )
        for index in range(8)
    ]
    replace_chunks(db, document.id, chunks)
    hits = VectorStore().search(db, [1.0] + [0.0] * 383, top_k=3)
    assert len(hits) == 3
