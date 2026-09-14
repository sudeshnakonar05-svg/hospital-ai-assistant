"""Appointment CRUD operations."""

from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


def get_by_id(db: Session, appointment_id: int) -> Appointment | None:
    """Fetch an appointment by id."""
    return db.get(Appointment, appointment_id)


def find_conflicting_appointment(
    db: Session,
    doctor_id: int,
    appointment_date: date,
    appointment_time: str,
    exclude_id: int | None = None,
) -> Appointment | None:
    """Check for an existing non-cancelled booking for the same doctor/date/time."""
    stmt = (
        select(Appointment)
        .where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_time == appointment_time,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
    )
    if exclude_id:
        stmt = stmt.where(Appointment.id != exclude_id)
    return db.execute(stmt).scalars().first()


def list_appointments(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    doctor_id: int | None = None,
    patient_id: int | None = None,
    status: str | None = None,
    appointment_date: date | None = None,
) -> list[Appointment]:
    """Return a page of appointments with optional filters."""
    stmt = select(Appointment)
    if doctor_id is not None:
        stmt = stmt.where(Appointment.doctor_id == doctor_id)
    if patient_id is not None:
        stmt = stmt.where(Appointment.patient_id == patient_id)
    if status is not None:
        stmt = stmt.where(Appointment.status == status)
    if appointment_date is not None:
        stmt = stmt.where(Appointment.appointment_date == appointment_date)
    stmt = stmt.offset(skip).limit(limit).order_by(Appointment.id.desc())
    return list(db.execute(stmt).scalars().all())


def create_appointment(db: Session, payload: AppointmentCreate) -> Appointment:
    """Create an appointment."""
    data = payload.model_dump()
    appointment = Appointment(**data)
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def update_appointment(
    db: Session, appointment: Appointment, payload: AppointmentUpdate
) -> Appointment:
    """Apply an appointment update."""
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(appointment, key, value)
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def delete_appointment(db: Session, appointment: Appointment) -> None:
    """Delete an appointment."""
    db.delete(appointment)
    db.commit()
