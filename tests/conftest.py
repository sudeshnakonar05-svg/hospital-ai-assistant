"""Shared pytest fixtures. Environment must be set before app imports."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Generator

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ["JWT_SECRET_KEY"] = "unit-test-jwt-secret-key-must-be-long-enough"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["LLM_PROVIDER"] = "retrieval_only"
os.environ["ADMIN_EMAIL"] = "admin@hospital.com"
os.environ["ADMIN_PASSWORD"] = "ChangeMeAdmin123!"
os.environ["ADMIN_FULL_NAME"] = "System Administrator"
os.environ["FIRST_SUPERUSER_EMAIL"] = "admin@hospital.com"
os.environ["FIRST_SUPERUSER_PASSWORD"] = "ChangeMeAdmin123!"
os.environ["FIRST_SUPERUSER_FULL_NAME"] = "System Administrator"
os.environ["RAG_TOP_K"] = "3"
os.environ["RAG_MIN_SCORE"] = "0.0"
os.environ["GROQ_API_KEY"] = ""
os.environ["EMBEDDING_DIM"] = "384"

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import *  # noqa: E402,F403
from app.services.embedding import EmbeddingService  # noqa: E402
from app.services import vector_store  # noqa: E402
import re


def _fake_vector(text: str, dim: int = 384) -> list[float]:
    """Deterministic bag-of-words embedding used in tests."""
    vector = np.zeros(dim, dtype=float)
    for token in re.findall(r"\w+", text.lower()):
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        index = int(digest, 16) % dim
        vector[index] += 1.0
    norm = np.linalg.norm(vector) or 1.0
    return (vector / norm).tolist()


@pytest.fixture(autouse=True)
def _fake_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid downloading heavy models during tests."""
    def embed(self: EmbeddingService, texts: list[str]) -> list[list[float]]:  # noqa: ARG002
        return [_fake_vector(text) for text in texts]

    def embed_query(self: EmbeddingService, text: str) -> list[float]:  # noqa: ARG002
        return _fake_vector(text)

    monkeypatch.setattr(EmbeddingService, "embed", embed)
    monkeypatch.setattr(EmbeddingService, "embed_query", embed_query)


@pytest.fixture(autouse=True)
def _isolated_storage(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Write uploads and vector files into a temp directory per test."""
    settings = get_settings()
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr(settings, "VECTOR_INDEX_PATH", str(tmp_path / "index.faiss"))
    monkeypatch.setattr(settings, "VECTOR_METADATA_PATH", str(tmp_path / "metadata.json"))
    monkeypatch.setattr(settings, "LLM_PROVIDER", "retrieval_only")
    monkeypatch.setattr(vector_store, "_global_vector_store", None)


@pytest.fixture(autouse=True)
def _reset_schema() -> Generator[None, None, None]:
    """Recreate ORM tables so tests do not leak rows."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """Yield a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client() -> TestClient:
    """HTTP test client."""
    return TestClient(app)


@pytest.fixture()
def admin_token(client: TestClient) -> str:
    """Login as the bootstrap admin user."""
    from app.crud.user import create_superuser
    from app.db.session import SessionLocal

    settings = get_settings()
    email = settings.effective_admin_email
    password = settings.effective_admin_password
    full_name = settings.effective_admin_full_name

    session = SessionLocal()
    try:
        create_superuser(
            session,
            email=email,
            password=password,
            full_name=full_name,
        )
    finally:
        session.close()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture()
def auth_headers(admin_token: str) -> dict[str, str]:
    """Authorization header for the admin user."""
    return {"Authorization": f"Bearer {admin_token}"}
