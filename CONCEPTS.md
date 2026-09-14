# Core Concepts

This document explains the ideas behind the Hospital Knowledge and Appointment Assistant.

## What is RAG?

Retrieval-Augmented Generation (RAG) is a pattern that answers a question in two steps:

1. **Retrieve** the most relevant passages from a hospital knowledge base (policies, department guides, visiting hours).
2. **Generate** an answer using only those passages (via Groq) or by quoting them (retrieval-only mode).

RAG reduces hallucination because the model is grounded in uploaded documents instead of inventing hospital rules. Every chat answer in this project also returns **source references** (filename, chunk index, similarity score, excerpt).

## What is chunking?

Chunking splits a long document into smaller overlapping pieces before embedding. A 20-page policy is too large to search as one blob: the embedding would mix many topics and retrieval would be noisy.

This app uses character chunking (`RAG_CHUNK_SIZE`, default 800) with overlap (`RAG_CHUNK_OVERLAP`, default 150) so neighboring chunks share context. Each chunk is stored in PostgreSQL (`knowledge_chunks`) with its embedding.

## What is embedding?

An embedding is a list of floating-point numbers that represents the *meaning* of a text snippet. Similar sentences land close together in that vector space.

This project uses **Sentence Transformers** (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions). The same model embeds both uploaded chunks and user questions so they can be compared.

## What is vector search?

Vector search finds the nearest embeddings to a query vector. On PostgreSQL this uses **pgvector** cosine distance (`<=>`). `RAG_TOP_K` (and an optional per-request `top_k`) limits how many chunks are returned.

Example: a question about “ICU visiting hours” is embedded, then the database returns the top-k policy chunks whose vectors are closest to that query. Those chunks become the RAG context.

Tests run against SQLite, which has no pgvector, so search falls back to in-process cosine similarity. Production uses PostgreSQL + pgvector.

## Why JWT is used?

JSON Web Tokens let the API stay **stateless**. After login, the server signs `{sub: email, role, uid, exp}` with `JWT_SECRET_KEY` (HS256). Protected routes read the `Authorization: Bearer` header, verify the signature, and load the user.

Benefits for this hospital API:

- Passwords are not sent on every request (only bcrypt hashes are stored).
- Staff/admin vs patient **role-based access** is encoded in the token and re-checked in the database.
- Swagger “Authorize” works with the OAuth2 password form that returns the same JWT.

The secret must stay in `.env` and never be committed. If it leaks, anyone can forge tokens.

## Why FastAPI is used?

FastAPI is a Python web framework built on Starlette and Pydantic. It fits this project because:

- **OpenAPI / Swagger** (`/docs`) is generated from type hints and Pydantic models.
- **Async + WebSockets** support the browser chat UI with status events.
- **Dependency injection** makes JWT auth and database sessions reusable.
- Validation and HTTP status codes are consistent across CRUD, uploads, and chat.

Together with SQLAlchemy, Alembic, and PostgreSQL JSONB, FastAPI gives a typed REST API that students can inspect in Swagger without a separate frontend for hospital CRUD.
