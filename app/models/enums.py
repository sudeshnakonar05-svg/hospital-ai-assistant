"""Shared enums for hospital domain models."""

import enum

from sqlalchemy import Enum as SAEnum


def sa_enum(enum_cls: type[enum.Enum], name: str) -> SAEnum:
    """SQLAlchemy enum that stores values (admin) not names (ADMIN)."""
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda members: [item.value for item in members],
        native_enum=False,  # Use standard varchar for portability across Postgres/SQLite without pg types
        validate_strings=True,
    )


class UserRole(str, enum.Enum):
    """Application roles used for RBAC."""

    ADMIN = "admin"
    STAFF = "staff"
    USER = "user"
    PATIENT = "patient"
    DOCTOR = "doctor"


class AppointmentStatus(str, enum.Enum):
    """Lifecycle states for an appointment."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class DocumentStatus(str, enum.Enum):
    """Indexing lifecycle for uploaded knowledge files."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    INDEXED = "indexed"
    FAILED = "failed"


class ChatRole(str, enum.Enum):
    """Roles in a chat transcript."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
