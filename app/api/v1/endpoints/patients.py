"""Patient CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff_or_admin
from app.crud import patient as patient_crud
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate

router = APIRouter()


@router.get("", response_model=list[PatientRead], summary="List patients")
def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PatientRead]:
    """List patients. Non-staff users only see their own profile if linked."""
    patients = patient_crud.list_patients(db, skip=skip, limit=limit)
    if current_user.role in (UserRole.USER, UserRole.PATIENT):
        return [p for p in patients if p.user_id == current_user.id]
    return patients


@router.get("/{patient_id}", response_model=PatientRead, summary="Get a patient")
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatientRead:
    """Fetch one patient with RBAC."""
    patient = patient_crud.get_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    if current_user.role in (UserRole.USER, UserRole.PATIENT) and patient.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return patient


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED, summary="Create a patient")
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff_or_admin),
) -> PatientRead:
    """Create a patient (staff/admin)."""
    if payload.medical_record_number and patient_crud.get_by_mrn(db, payload.medical_record_number):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MRN already exists")
    return patient_crud.create_patient(db, payload)


@router.put("/{patient_id}", response_model=PatientRead, summary="Update a patient (full)")
def update_patient_put(
    patient_id: int,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff_or_admin),
) -> PatientRead:
    """Update a patient via PUT (staff/admin)."""
    patient = patient_crud.get_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient_crud.update_patient(db, patient, payload)


@router.patch("/{patient_id}", response_model=PatientRead, summary="Update a patient (partial)")
def update_patient_patch(
    patient_id: int,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff_or_admin),
) -> PatientRead:
    """Update a patient via PATCH (staff/admin)."""
    patient = patient_crud.get_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient_crud.update_patient(db, patient, payload)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a patient")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff_or_admin),
) -> None:
    """Delete a patient (staff/admin)."""
    patient = patient_crud.get_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    patient_crud.delete_patient(db, patient)
