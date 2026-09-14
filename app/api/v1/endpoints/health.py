"""Health and readiness endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()


@router.get("/health", summary="Liveness probe")
def health() -> dict[str, str]:
    """Return a simple liveness payload."""
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness probe")
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    """Verify the database connection."""
    db.execute(text("SELECT 1"))
    return {"status": "ready"}
