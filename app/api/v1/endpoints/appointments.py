"""Appointment CRUD endpoints."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud import appointment as appointment_crud
from app.crud import doctor as doctor_crud
from app.crud import patient as patient_crud
from app.db.session import get_db
from app.models.enums import AppointmentStatus, UserRole
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentUpdate

router = APIRouter()


@router.get("", response_model=list[AppointmentRead], summary="List appointments")
def list_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    doctor_id: int | None = None,
    patient_id: int | None = None,
    status_filter: str | None = Query(None, alias="status"),
    appointment_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AppointmentRead]:
    """List appointments with filtering."""
    if current_user.role in (UserRole.USER, UserRole.PATIENT):
        linked = [p for p in patient_crud.list_patients(db, limit=200) if p.user_id == current_user.id]
        if linked:
            patient_id = linked[0].id

    return appointment_crud.list_appointments(
        db,
        skip=skip,
        limit=limit,
        doctor_id=doctor_id,
        patient_id=patient_id,
        status=status_filter,
        appointment_date=appointment_date,
    )


@router.get("/{appointment_id}", response_model=AppointmentRead, summary="Get an appointment")
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AppointmentRead:
    """Fetch one appointment by ID."""
    appointment = appointment_crud.get_by_id(db, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return appointment


@router.post(
    "",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an appointment",
)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AppointmentRead:
    """Schedule an appointment."""
    doctor = doctor_crud.get_by_id(db, payload.doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor not found")
    patient = patient_crud.get_by_id(db, payload.patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient not found")

    # Prevent obvious duplicate bookings for the same doctor at the same date and time
    if payload.appointment_date and payload.appointment_time:
        conflict = appointment_crud.find_conflicting_appointment(
            db,
            doctor_id=payload.doctor_id,
            appointment_date=payload.appointment_date,
            appointment_time=payload.appointment_time,
        )
        if conflict is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This doctor already has an active appointment at this date and time",
            )

    return appointment_crud.create_appointment(db, payload)


@router.put("/{appointment_id}", response_model=AppointmentRead, summary="Update an appointment (full)")
def update_appointment_put(
    appointment_id: int,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AppointmentRead:
    """Update an appointment via PUT."""
    appointment = appointment_crud.get_by_id(db, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if payload.doctor_id is not None and doctor_crud.get_by_id(db, payload.doctor_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor not found")
    if payload.patient_id is not None and patient_crud.get_by_id(db, payload.patient_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient not found")

    doc_id = payload.doctor_id or appointment.doctor_id
    app_date = payload.appointment_date or appointment.appointment_date
    app_time = payload.appointment_time or appointment.appointment_time

    if payload.status != AppointmentStatus.CANCELLED:
        conflict = appointment_crud.find_conflicting_appointment(
            db, doctor_id=doc_id, appointment_date=app_date, appointment_time=app_time, exclude_id=appointment_id
        )
        if conflict is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflict: doctor already has an active appointment at this date and time",
            )

    return appointment_crud.update_appointment(db, appointment, payload)


@router.patch("/{appointment_id}", response_model=AppointmentRead, summary="Update an appointment (partial)")
def update_appointment_patch(
    appointment_id: int,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AppointmentRead:
    """Update an appointment via PATCH."""
    appointment = appointment_crud.get_by_id(db, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if payload.doctor_id is not None and doctor_crud.get_by_id(db, payload.doctor_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor not found")
    if payload.patient_id is not None and patient_crud.get_by_id(db, payload.patient_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient not found")

    doc_id = payload.doctor_id or appointment.doctor_id
    app_date = payload.appointment_date or appointment.appointment_date
    app_time = payload.appointment_time or appointment.appointment_time

    if payload.status is not None and payload.status != AppointmentStatus.CANCELLED:
        conflict = appointment_crud.find_conflicting_appointment(
            db, doctor_id=doc_id, appointment_date=app_date, appointment_time=app_time, exclude_id=appointment_id
        )
        if conflict is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflict: doctor already has an active appointment at this date and time",
            )

    return appointment_crud.update_appointment(db, appointment, payload)


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an appointment",
)
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    """Delete an appointment."""
    appointment = appointment_crud.get_by_id(db, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    appointment_crud.delete_appointment(db, appointment)
