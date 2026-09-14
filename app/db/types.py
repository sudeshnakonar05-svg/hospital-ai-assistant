"""Portable embedding column: pgvector on PostgreSQL, JSON elsewhere."""

from typing import Any

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON, TypeDecorator

from app.core.config import get_settings


class EmbeddingVector(TypeDecorator):
    """Store float embeddings as a pgvector Vector or JSON list."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector

            return dialect.type_descriptor(Vector(get_settings().EMBEDDING_DIM))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return list(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return list(value)


def json_type() -> Any:
    """Return JSONB on PostgreSQL and JSON on other dialects."""
    from sqlalchemy import JSON as SA_JSON

    return SA_JSON().with_variant(JSONB, "postgresql")
