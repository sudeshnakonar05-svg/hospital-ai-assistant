# Hospital Knowledge and Appointment Assistant — Core Concepts Guide

This guide explains the foundational technologies, architectures, and design decisions used in this project in clear, college-level terminology. It is designed to prepare you for presentations, viva voce examinations, and technical demonstrations.

---

## 1. What is RAG (Retrieval-Augmented Generation)?

**Retrieval-Augmented Generation (RAG)** is an AI architecture that enhances language models by retrieving relevant factual excerpts from an external, verified knowledge base before generating an answer.

### Why Standard LLMs Alone Fall Short:
- **Hallucination**: Standard models may invent plausible-sounding facts, fake clinic hours, or fabricated doctor names.
- **Knowledge Cutoff**: Models do not know your private hospital's policies, local phone numbers, or recent visiting rules.
- **Data Privacy**: You cannot retrain or fine-tune multi-billion-parameter models every time visiting hours change.

### The RAG Workflow:
```
User Question ("When can families visit ICU patients?")
                 │
                 ▼
         1. Emergency Guard Check (Safety check first)
                 │
                 ▼
         2. Embedding Generation (Vectorize question)
                 │
                 ▼
         3. FAISS Vector Search (Retrieve top-k chunks)
                 │
                 ▼
         4. Context Assembly (Combine prompt + official excerpts)
                 │
                 ▼
         5. Grounded Generation (Retrieval-only or Groq LLM)
                 │
                 ▼
         Final Answer + Cited Sources (Document & Chunk index)
```

By constraining the answer to retrieved excerpts, the system provides grounded, factual answers with verifiable citations.

---

## 2. What is Chunking?

**Chunking** is the process of splitting large documents (such as multi-page policy manuals or PDF handbooks) into smaller, coherent segments of text.

### Why Chunking is Essential:
1. **Semantic Precision**: When a document is 20 pages long, an embedding of the whole document blurs individual details. A 500-word chunk about "ICU Visiting Rules" maintains a sharp, focused semantic meaning.
2. **Context Window Limitations**: LLM prompt windows are finite. Chunking ensures we send only the 3 or 5 most relevant paragraphs instead of an entire 50-page manual.
3. **Retrieval Granularity**: When answering a query, users want exact citations (e.g., "From visiting_hours.txt, Chunk #1") rather than wading through entire handbooks.

### Overlapping Chunks:
By adding an overlap (e.g., 50 words between successive chunks), we avoid breaking sentences or context right at the boundary.

---

## 3. What is an Embedding?

An **embedding** is a dense numerical vector (a list of floating-point numbers, e.g., 384 dimensions) that captures the semantic meaning of a piece of text.

- In traditional keyword search, searching for "physician schedule" fails if the document only uses the word "doctor hours".
- In vector embeddings, models like `sentence-transformers/all-MiniLM-L6-v2` place "physician schedule" and "doctor hours" very close to each other in vector space because their semantic meanings are related.

Texts with similar meanings produce vectors with high cosine similarity (small angular distance).

---

## 4. What is Vector Search?

**Vector search** (also known as nearest-neighbor search) is the mathematical process of finding the vectors in a database that are closest in direction or distance to a query vector.

### Similarity Metrics:
- **Cosine Similarity**: Measures the cosine of the angle between two vectors:
  $$\text{Cosine Similarity} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$
- When vectors are L2-normalized (length = 1.0), the cosine similarity is simply the inner product (dot product $\mathbf{u} \cdot \mathbf{v}$). Values range from -1.0 to 1.0, where 1.0 denotes identical semantic orientation.

---

## 5. Why FAISS?

**FAISS (Facebook AI Similarity Search)** is a library developed by Meta for efficient similarity search and clustering of dense vectors.

### Advantages for this College Project:
1. **Lightweight & Self-Contained**: FAISS runs directly in Python via `faiss-cpu` without requiring specialized external microservices, cloud accounts, or complex server infrastructure.
2. **Standard PostgreSQL Compatibility**: Instead of requiring native C extensions (like `pgvector`) that often fail to compile on varied student laptops (Windows, macOS, Linux), FAISS indexes vectors cleanly on the filesystem while PostgreSQL stores relational records.
3. **Blazing Speed**: FAISS uses optimized C++ matrix multiplication and SIMD instruction sets, delivering sub-millisecond similarity search over thousands of chunks.
4. **Dual Persistence**: The index is saved to `data/vector_index/index.faiss` and metadata to `data/vector_index/metadata.json`, allowing easy inspection and backup.

---

## 6. Why JWT (JSON Web Tokens)?

**JSON Web Tokens (JWT)** provide a compact, stateless method for securely transmitting information between the client and the server.

### How it Works:
1. When a user logs in with valid credentials via `POST /api/v1/auth/login`, the server hashes the password with bcrypt, verifies it, and signs a JWT containing claims (`sub` = email, `role` = user role, `exp` = expiration time).
2. The client receives this token and includes it in the `Authorization: Bearer <token>` header for subsequent requests.
3. The server validates the cryptographic signature using `JWT_SECRET_KEY` without making repeated session lookups in a shared database or cache.

### Security Best Practices:
- Passwords and sensitive health records are never stored in JWT payloads.
- Role-based authorization (`require_admin`, `require_staff_or_admin`) checks user roles on the backend for every protected route.

---

## 7. Why FastAPI?

**FastAPI** is a modern, high-performance web framework for building APIs with Python 3.10+ based on standard Python type hints.

### Key Benefits:
1. **Fast Development**: Minimal boilerplate with rapid turnaround time.
2. **Pydantic Validation**: Automatic request data validation and serialization with descriptive error messages.
3. **Automatic OpenAPI/Swagger Documentation**: Interactive API documentation generated at `/docs` and `/redoc` out of the box.
4. **Dependency Injection**: Reusable dependencies for authentication, role enforcement, and database sessions (`Depends(get_db)`, `Depends(get_current_user)`).
5. **Native Async**: Async/await support enables concurrent file uploads, external LLM calls, and WebSocket connections.

---

## 8. Why PostgreSQL?

**PostgreSQL** is an enterprise-grade, open-source object-relational database system known for reliability, data integrity, and standards compliance.

### Why It Fits Our Backend:
1. **Relational Integrity**: Foreign keys ensure referential integrity between `departments`, `doctors`, `patients`, and `appointments`.
2. **ACID Transactions**: Ensures appointments cannot be booked concurrently with overlapping time slots, maintaining consistency.
3. **JSON/JSONB Support**: Stores flexible metadata alongside structured tables without requiring separate NoSQL stores.
4. **SQLAlchemy & Alembic Integration**: Industry-standard ORM modeling with version-controlled database migrations.
