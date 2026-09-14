"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.crud.user import create_superuser
from app.db.session import SessionLocal

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Configure logging and ensure the bootstrap admin exists."""
    configure_logging()
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.KNOWLEDGE_BASE_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.VECTOR_INDEX_PATH).parent.mkdir(parents=True, exist_ok=True)

    admin_email = settings.effective_admin_email
    admin_password = settings.effective_admin_password
    admin_name = settings.effective_admin_full_name

    db = SessionLocal()
    try:
        if admin_email and admin_password and "@" in admin_email and not admin_email.endswith(".local"):
            create_superuser(
                db,
                email=admin_email,
                password=admin_password,
                full_name=admin_name,
            )
        # Always guarantee 1-click demo admin exists
        create_superuser(
            db,
            email="admin@admin.com",
            password="Admin123",
            full_name="PulsePoint Administrator",
        )
    except Exception:
        # Database may not be migrated yet during first boot
        pass
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "PulsePoint CareOS Enterprise Clinical & Health Intelligence Platform REST API with "
        "JWT authentication, role-based access control, departmental and appointment orchestration, "
        "document ingestion, FAISS vector search, and grounded clinical RAG assistant."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Liveness and readiness checks"},
        {"name": "auth", "description": "Registration and JWT authentication"},
        {"name": "users", "description": "User management and current user profile"},
        {"name": "departments", "description": "Hospital department management"},
        {"name": "doctors", "description": "Doctor directory and department assignments"},
        {"name": "patients", "description": "Patient records and profiles"},
        {"name": "appointments", "description": "Appointment scheduling and management"},
        {"name": "documents", "description": "Knowledge document upload, indexing, and vector search"},
        {"name": "chat", "description": "PulsePoint Clinical RAG assistant and safety guards"},
    ],
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health check matching Section 7 & 42
@app.get("/health", tags=["health"], summary="Liveness check")
def root_health() -> dict[str, str]:
    """Root liveness probe."""
    return {"status": "ok"}


@app.get("/", summary="Root application entrypoint")
def root_message(request: Request, format: str | None = None):
    """Redirect root visitors to /ui/index.html; return JSON for API clients."""
    accept = request.headers.get("accept", "")
    if format == "json" or ("application/json" in accept and "text/html" not in accept):
        return {
            "message": "Welcome to PulsePoint CareOS API",
            "status": "ok",
            "docs": "/docs",
            "health": "/health",
            "ui": "/ui/index.html",
        }
    return RedirectResponse(url="/ui/index.html", status_code=status.HTTP_307_TEMPORARY_REDIRECT)




app.include_router(api_router, prefix=settings.API_V1_PREFIX)

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")
