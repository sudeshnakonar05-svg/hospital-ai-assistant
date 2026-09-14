"""FAISS vector store and similarity search."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

from app.core.config import get_settings
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument

logger = logging.getLogger(__name__)


@dataclass
class SearchHit:
    """A ranked chunk from vector search."""

    chunk: KnowledgeChunk | Any
    document: KnowledgeDocument | Any
    score: float


class VectorStore:
    """Persist embeddings in FAISS and retrieve top-k nearest chunks."""

    def __init__(
        self,
        index_path: str | None = None,
        metadata_path: str | None = None,
        dim: int | None = None,
    ) -> None:
        settings = get_settings()
        self.index_path = Path(index_path or settings.VECTOR_INDEX_PATH)
        self.metadata_path = Path(metadata_path or settings.VECTOR_METADATA_PATH)
        self.dim = dim or settings.EMBEDDING_DIM
        self.index: Any = None
        self.metadata: list[dict[str, Any]] = []
        self._ensure_loaded()

    def _ensure_loaded(self) -> None:
        """Attempt to load existing FAISS index and metadata if files exist."""
        if self.index_path.exists() and self.metadata_path.exists():
            self.load_index()

    def _create_empty_index(self) -> Any:
        """Create a new FAISS inner-product index (cosine similarity when normalized)."""
        if faiss is None:
            logger.warning("faiss is not installed; vector search running in memory fallback mode")
            return None
        return faiss.IndexFlatIP(self.dim)

    def add_vectors(
        self,
        vectors: list[list[float]] | np.ndarray,
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Add embedding vectors and their corresponding metadata."""
        if len(vectors) == 0:
            return
        arr = np.array(vectors, dtype="float32")
        if arr.ndim == 1:
            arr = np.expand_dims(arr, axis=0)

        # L2 normalize vectors for cosine similarity via inner product
        faiss_available = faiss is not None
        if faiss_available:
            faiss.normalize_L2(arr)
            if self.index is None:
                self.index = self._create_empty_index()
            self.index.add(arr)
        else:
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            arr = arr / norms

        for meta in metadatas:
            self.metadata.append(dict(meta))

    def replace_document_vectors(
        self,
        vectors: list[list[float]] | np.ndarray,
        metadatas: list[dict[str, Any]],
        document_id: int,
    ) -> None:
        """Replace all indexed vectors for one document without leaving stale chunks."""
        if self.index is None or faiss is None:
            self.metadata = [meta for meta in self.metadata if meta.get("document_id") != document_id]
            self.add_vectors(vectors, metadatas)
            return

        retained_vectors: list[np.ndarray] = []
        retained_metadata: list[dict[str, Any]] = []
        for index, metadata in enumerate(self.metadata):
            if metadata.get("document_id") == document_id:
                continue
            retained_vectors.append(self.index.reconstruct(index))
            retained_metadata.append(metadata)

        self.index = self._create_empty_index()
        self.metadata = []
        if retained_vectors:
            self.add_vectors(np.array(retained_vectors, dtype="float32"), retained_metadata)
        self.add_vectors(vectors, metadatas)

    def remove_document_vectors(self, document_id: int) -> None:
        """Remove all indexed vectors for a document and persist the rebuilt index."""
        if not self.metadata:
            return
        if self.index is None or faiss is None:
            self.metadata = [meta for meta in self.metadata if meta.get("document_id") != document_id]
            return

        retained_vectors = []
        retained_metadata = []
        for index, metadata in enumerate(self.metadata):
            if metadata.get("document_id") == document_id:
                continue
            retained_vectors.append(self.index.reconstruct(index))
            retained_metadata.append(metadata)

        self.index = self._create_empty_index()
        self.metadata = []
        if retained_vectors:
            self.add_vectors(np.array(retained_vectors, dtype="float32"), retained_metadata)

    def save_index(
        self,
        index_path: str | None = None,
        metadata_path: str | None = None,
    ) -> None:
        """Save FAISS index and metadata to disk."""
        target_idx = Path(index_path) if index_path else self.index_path
        target_meta = Path(metadata_path) if metadata_path else self.metadata_path

        target_idx.parent.mkdir(parents=True, exist_ok=True)
        target_meta.parent.mkdir(parents=True, exist_ok=True)

        if self.index is not None and faiss is not None:
            faiss.write_index(self.index, str(target_idx))
            logger.info("Saved FAISS index to %s", target_idx)

        with open(target_meta, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2)
        logger.info("Saved vector metadata to %s", target_meta)

    def load_index(
        self,
        index_path: str | None = None,
        metadata_path: str | None = None,
    ) -> bool:
        """Load FAISS index and metadata from disk."""
        target_idx = Path(index_path) if index_path else self.index_path
        target_meta = Path(metadata_path) if metadata_path else self.metadata_path

        if not target_idx.exists() or not target_meta.exists():
            logger.info(
                "Vector index files do not exist at %s or %s. Vector store is currently empty.",
                target_idx,
                target_meta,
            )
            return False

        try:
            if faiss is not None:
                self.index = faiss.read_index(str(target_idx))
            with open(target_meta, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            logger.info("Loaded FAISS index with %d items", len(self.metadata))
            return True
        except Exception as exc:
            logger.warning("Could not load FAISS index: %s", exc)
            return False

    def search_index(
        self,
        query_vector: list[float] | np.ndarray,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Search the FAISS index for top-k similar chunks."""
        if self.index is None or len(self.metadata) == 0:
            if not self.load_index() or self.index is None or len(self.metadata) == 0:
                logger.info("Vector index is empty. No documents indexed yet.")
                return []

        q = np.array([query_vector], dtype="float32")
        if faiss is not None:
            faiss.normalize_L2(q)
            k = min(top_k, len(self.metadata))
            distances, indices = self.index.search(q, k)
            hits: list[dict[str, Any]] = []
            for score, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self.metadata):
                    continue
                meta = self.metadata[idx]
                hits.append({
                    "content": meta.get("content", ""),
                    "source": meta.get("source", meta.get("document", "unknown")),
                    "document": meta.get("document", meta.get("source", "unknown")),
                    "chunk": meta.get("chunk", meta.get("chunk_index", 0)),
                    "chunk_index": meta.get("chunk_index", meta.get("chunk", 0)),
                    "document_id": meta.get("document_id", 0),
                    "score": float(score),
                    "metadata": meta,
                })
            return hits
        return []

    def search(
        self,
        db: Any,
        query_embedding: list[float],
        top_k: int | None = None,
    ) -> list[SearchHit]:
        """Search adapter for compatibility with DB session callers."""
        settings = get_settings()
        k = top_k or settings.RAG_TOP_K
        results = self.search_index(query_embedding, top_k=k)
        hits: list[SearchHit] = []

        for item in results:
            doc_id = item.get("document_id")
            chunk_idx = item.get("chunk_index", 0)
            content = item.get("content", "")
            source = item.get("source", "")
            score = item.get("score", 0.0)

            chunk = None
            document = None
            if db is not None and hasattr(db, "get") and doc_id:
                try:
                    document = db.get(KnowledgeDocument, doc_id)
                except Exception:
                    pass

            if db is not None and doc_id and document is None:
                continue

            if chunk is None:
                # Synthetic chunk object matching interface
                class SyntheticChunk:
                    def __init__(self, doc_id, c_idx, text, extra_meta):
                        self.id = 0
                        self.document_id = doc_id
                        self.chunk_index = c_idx
                        self.content = text
                        self.extra = extra_meta
                        self.chunk_metadata = extra_meta

                chunk = SyntheticChunk(doc_id, chunk_idx, content, {"source": source})

            if document is None:
                class SyntheticDoc:
                    def __init__(self, name):
                        self.original_name = name
                        self.filename = name

                document = SyntheticDoc(source)

            hits.append(SearchHit(chunk=chunk, document=document, score=score))

        # If FAISS had no hits but DB has chunks (in unit test environments), fallback to DB
        if not hits and db is not None and hasattr(db, "execute"):
            from app.crud import knowledge_document as doc_crud
            db_chunks = doc_crud.list_chunks_with_embeddings(db)
            if db_chunks:
                query = np.array(query_embedding, dtype=float)
                query_norm = np.linalg.norm(query) or 1.0
                scored = []
                for ch in db_chunks:
                    if ch.embedding:
                        vec = np.array(ch.embedding, dtype=float)
                        denom = (np.linalg.norm(vec) * query_norm) or 1.0
                        sc = float(np.dot(query, vec) / denom)
                        doc = db.get(KnowledgeDocument, ch.document_id)
                        scored.append(SearchHit(chunk=ch, document=doc, score=sc))
                scored.sort(key=lambda h: h.score, reverse=True)
                return scored[:k]

        return hits


_global_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Return a process-wide VectorStore instance."""
    global _global_vector_store
    if _global_vector_store is None:
        _global_vector_store = VectorStore()
    return _global_vector_store
