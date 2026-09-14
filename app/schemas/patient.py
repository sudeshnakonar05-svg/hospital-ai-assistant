"""Patient schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PatientCreate(BaseModel):
    """Create a patient record."""

    name: str | None = None
    full_name: str | None = None
    date_of_birth: date
    gender: str | None = None
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = None
    address: str | None = None
    medical_record_number: str | None = None
    user_id: int | None = None
    extra: dict[str, Any] | None = None

    @model_validator(mode="after")
    def sync_name(self) -> "PatientCreate":
        if not self.name and not self.full_name:
            raise ValueError("Patient name is required")
        if not self.name and self.full_name:
            self.name = self.full_name
        if not self.full_name and self.name:
            self.full_name = self.name
        return self


class PatientUpdate(BaseModel):
    """Patient update."""

    name: str | None = None
    full_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    medical_record_number: str | None = None
    user_id: int | None = None
    extra: dict[str, Any] | None = None

    @model_validator(mode="after")
    def sync_name(self) -> "PatientUpdate":
        if self.name and not self.full_name:
            self.full_name = self.name
        elif self.full_name and not self.name:
            self.name = self.full_name
        return self


class PatientRead(BaseModel):
    """Patient response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    full_name: str
    date_of_birth: date
    gender: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    medical_record_number: str | None = None
    user_id: int | None = None
    extra: dict[str, Any] | None = None
    created_at: datetime | None = None
