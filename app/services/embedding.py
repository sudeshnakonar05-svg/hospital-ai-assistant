"""Sentence-Transformers embedding service."""

from functools import lru_cache
from typing import Sequence

import numpy as np

from app.core.config import get_settings


class EmbeddingService:
    """Generate dense vectors for documents and queries."""

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None

    @property
    def model(self):
        """Lazily load the transformer so tests can stub embed()."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed one or more texts and L2-normalize the vectors."""
        if not texts:
            return []
        vectors = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.astype(float).tolist() for vector in np.atleast_2d(vectors)]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""
        return self.embed([text])[0]


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """Return a process-wide embedding service."""
    return EmbeddingService()
