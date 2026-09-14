"""Doctor schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DoctorCreate(BaseModel):
    """Create a doctor record."""

    department_id: int
    name: str | None = None
    full_name: str | None = None
    specialization: str = Field(min_length=2, max_length=255)
    phone: str | None = None
    email: str | None = None
    is_active: bool = True
    license_number: str | None = None
    user_id: int | None = None
    extra: dict[str, Any] | None = None

    @model_validator(mode="after")
    def populate_name(self) -> "DoctorCreate":
        if not self.name and not self.full_name:
            raise ValueError("Doctor name is required")
        if not self.name and self.full_name:
            self.name = self.full_name
        if not self.full_name and self.name:
            self.full_name = self.name
        return self


class DoctorUpdate(BaseModel):
    """Doctor update schema."""

    department_id: int | None = None
    name: str | None = None
    full_name: str | None = None
    specialization: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool | None = None
    license_number: str | None = None
    user_id: int | None = None
    extra: dict[str, Any] | None = None

    @model_validator(mode="after")
    def sync_name(self) -> "DoctorUpdate":
        if self.name and not self.full_name:
            self.full_name = self.name
        elif self.full_name and not self.name:
            self.name = self.full_name
        return self


class DoctorRead(BaseModel):
    """Doctor response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    full_name: str
    specialization: str
    department_id: int
    phone: str | None = None
    email: str | None = None
    is_active: bool = True
    license_number: str | None = None
    user_id: int | None = None
    extra: dict[str, Any] | None = None
    created_at: datetime | None = None
