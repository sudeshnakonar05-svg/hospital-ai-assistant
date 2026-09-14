"""Patient CRUD operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


def get_by_id(db: Session, patient_id: int) -> Patient | None:
    """Fetch a patient by id."""
    return db.get(Patient, patient_id)


def get_by_mrn(db: Session, medical_record_number: str) -> Patient | None:
    """Fetch a patient by medical record number."""
    if not medical_record_number:
        return None
    stmt = select(Patient).where(Patient.medical_record_number == medical_record_number)
    return db.execute(stmt).scalar_one_or_none()


def list_patients(db: Session, skip: int = 0, limit: int = 50) -> list[Patient]:
    """Return a page of patients."""
    stmt = select(Patient).offset(skip).limit(limit).order_by(Patient.id)
    return list(db.execute(stmt).scalars().all())


def create_patient(db: Session, payload: PatientCreate) -> Patient:
    """Create a patient."""
    data = payload.model_dump()
    name = data.pop("name", None) or data.pop("full_name", None)
    data.pop("full_name", None)
    patient = Patient(name=name, **data)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def update_patient(db: Session, patient: Patient, payload: PatientUpdate) -> Patient:
    """Apply a partial patient update."""
    data = payload.model_dump(exclude_unset=True)
    if "full_name" in data and "name" not in data:
        data["name"] = data.pop("full_name")
    elif "full_name" in data:
        data.pop("full_name")
    for key, value in data.items():
        setattr(patient, key, value)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def delete_patient(db: Session, patient: Patient) -> None:
    """Delete a patient."""
    db.delete(patient)
    db.commit()
