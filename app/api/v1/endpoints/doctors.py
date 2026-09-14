"""Doctor CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff_or_admin
from app.crud import department as department_crud
from app.crud import doctor as doctor_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.doctor import DoctorCreate, DoctorRead, DoctorUpdate

router = APIRouter()


@router.get("", response_model=list[DoctorRead], summary="List doctors")
def list_doctors(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    department_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DoctorRead]:
    """List doctors, optionally filtered by department."""
    return doctor_crud.list_doctors(db, skip=skip, limit=limit, department_id=department_id)


@router.get("/{doctor_id}", response_model=DoctorRead, summary="Get a doctor")
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DoctorRead:
    """Fetch one doctor by ID."""
    doctor = doctor_crud.get_by_id(db, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return doctor


@router.post("", response_model=DoctorRead, status_code=status.HTTP_201_CREATED, summary="Create a doctor")
def create_doctor(
    payload: DoctorCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff_or_admin),
) -> DoctorRead:
    """Create a doctor record (staff/admin)."""
    if department_crud.get_by_id(db, payload.department_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department not found")
    if payload.license_number and doctor_crud.get_by_license(db, payload.license_number):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="License number already exists")
    return doctor_crud.create_doctor(db, payload)


@router.put("/{doctor_id}", response_model=DoctorRead, summary="Update a doctor (full)")
def update_doctor_put(
    doctor_id: int,
    payload: DoctorUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff_or_admin),
) -> DoctorRead:
    """Update a doctor via PUT (staff/admin)."""
    doctor = doctor_crud.get_by_id(db, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    if payload.department_id is not None and department_crud.get_by_id(db, payload.department_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department not found")
    return doctor_crud.update_doctor(db, doctor, payload)


@router.patch("/{doctor_id}", response_model=DoctorRead, summary="Update a doctor (partial)")
def update_doctor_patch(
    doctor_id: int,
    payload: DoctorUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff_or_admin),
) -> DoctorRead:
    """Update a doctor via PATCH (staff/admin)."""
    doctor = doctor_crud.get_by_id(db, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    if payload.department_id is not None and department_crud.get_by_id(db, payload.department_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department not found")
    return doctor_crud.update_doctor(db, doctor, payload)


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a doctor")
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff_or_admin),
) -> None:
    """Delete a doctor (staff/admin)."""
    doctor = doctor_crud.get_by_id(db, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    doctor_crud.delete_doctor(db, doctor)
