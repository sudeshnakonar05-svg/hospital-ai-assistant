"""User ORM model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole, sa_enum


class User(Base):
    """Registered application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        sa_enum(UserRole, "userrole"), default=UserRole.USER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    doctor_profile: Mapped[Optional["Doctor"]] = relationship(back_populates="user", uselist=False)
    patient_profile: Mapped[Optional["Patient"]] = relationship(back_populates="user", uselist=False)
    documents: Mapped[list["KnowledgeDocument"]] = relationship(back_populates="uploader")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user")
