"""Appointment schemas."""

from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import AppointmentStatus


class AppointmentCreate(BaseModel):
    """Schedule an appointment."""

    doctor_id: int
    patient_id: int
    appointment_date: date | None = None
    appointment_time: str | None = None
    scheduled_at: datetime | None = None
    reason: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=4000)
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    extra: dict[str, Any] | None = None

    @model_validator(mode="after")
    def populate_datetime(self) -> "AppointmentCreate":
        if self.scheduled_at and not self.appointment_date:
            self.appointment_date = self.scheduled_at.date()
        if self.scheduled_at and not self.appointment_time:
            self.appointment_time = self.scheduled_at.strftime("%H:%M")
        if self.appointment_date and self.appointment_time and not self.scheduled_at:
            try:
                parts = self.appointment_time.split(":")
                h, m = int(parts[0]), int(parts[1])
                self.scheduled_at = datetime.combine(self.appointment_date, time(h, m))
            except Exception:
                pass
        if not self.appointment_date:
            raise ValueError("appointment_date or scheduled_at is required")
        if not self.appointment_time:
            self.appointment_time = "09:00"
        return self


class AppointmentUpdate(BaseModel):
    """Appointment update schema."""

    doctor_id: int | None = None
    patient_id: int | None = None
    appointment_date: date | None = None
    appointment_time: str | None = None
    scheduled_at: datetime | None = None
    status: AppointmentStatus | None = None
    reason: str | None = None
    notes: str | None = None
    extra: dict[str, Any] | None = None

    @model_validator(mode="after")
    def sync_datetime(self) -> "AppointmentUpdate":
        if self.scheduled_at and not self.appointment_date:
            self.appointment_date = self.scheduled_at.date()
        if self.scheduled_at and not self.appointment_time:
            self.appointment_time = self.scheduled_at.strftime("%H:%M")
        return self


class AppointmentRead(BaseModel):
    """Appointment response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    patient_id: int
    appointment_date: date
    appointment_time: str
    scheduled_at: datetime | None = None
    status: AppointmentStatus
    reason: str | None = None
    notes: str | None = None
    extra: dict[str, Any] | None = None
    created_at: datetime | None = None
