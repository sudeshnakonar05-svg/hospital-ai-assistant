# PulsePoint CareOS

An intelligent, next-generation clinical operations & healthcare AI platform with grounded RAG clinical intelligence, appointment scheduling, medical directory, patient record management, and emergency safety triage.

## What it does

- Manage healthcare data: clinical departments, medical specialists, patient profiles, and appointments
- Support secure authentication and role-based access control (RBAC: Admin, Staff, Patient)
- Upload, chunk, and index medical guidelines and policy documents with FAISS dense vector search
- Answer medical and hospital queries with grounded retrieval-augmented generation (RAG)
- Immediate safety guardrails intercepting emergencies with urgent triage guidance

## Tech stack

- Python 3.10+
- FastAPI
- PostgreSQL + SQLAlchemy
- Alembic
- FAISS
- Sentence transformers
- JWT auth

## Quick start (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env

# Make sure PostgreSQL is running and the database exists
createdb hospital_ai

alembic upgrade head
python scripts/create_admin.py
python scripts/ingest_knowledge_base.py
uvicorn app.main:app --reload
```

Open the app at:
- API docs: http://127.0.0.1:8000/docs
- UI: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health

## Demo flow

1. Register or log in through the API or UI.
2. Create a department and doctor.
3. Create a patient.
4. Book an appointment.
5. Ask a grounded question in the chatbot.
6. Try an unrelated or emergency question to see the guardrails.

## Testing

```bash
pytest -q
```

## Notes

- Default chatbot mode is `retrieval_only` and does not require an external API key.
- If you want Groq-backed answers, set `LLM_PROVIDER=groq` and add `GROQ_API_KEY`.
- The emergency guard blocks urgent medical scenarios and directs users to emergency care.

## Project layout

```text
app/          FastAPI application and business logic
alembic/      database migrations
data/         knowledge base and vector index
scripts/      setup and ingestion helpers
tests/        unit and integration tests
```
