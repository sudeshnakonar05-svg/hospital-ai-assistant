"""Doctor CRUD operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate, DoctorUpdate


def get_by_id(db: Session, doctor_id: int) -> Doctor | None:
    """Fetch a doctor by id."""
    return db.get(Doctor, doctor_id)


def get_by_license(db: Session, license_number: str) -> Doctor | None:
    """Fetch a doctor by license number."""
    if not license_number:
        return None
    stmt = select(Doctor).where(Doctor.license_number == license_number)
    return db.execute(stmt).scalar_one_or_none()


def list_doctors(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    department_id: int | None = None,
) -> list[Doctor]:
    """Return a page of doctors, optionally filtered by department."""
    stmt = select(Doctor)
    if department_id is not None:
        stmt = stmt.where(Doctor.department_id == department_id)
    stmt = stmt.offset(skip).limit(limit).order_by(Doctor.id)
    return list(db.execute(stmt).scalars().all())


def create_doctor(db: Session, payload: DoctorCreate) -> Doctor:
    """Create a doctor."""
    data = payload.model_dump()
    name = data.pop("name", None) or data.pop("full_name", None)
    data.pop("full_name", None)
    doctor = Doctor(name=name, **data)
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def update_doctor(db: Session, doctor: Doctor, payload: DoctorUpdate) -> Doctor:
    """Apply a doctor update."""
    data = payload.model_dump(exclude_unset=True)
    if "full_name" in data and "name" not in data:
        data["name"] = data.pop("full_name")
    elif "full_name" in data:
        data.pop("full_name")
    for key, value in data.items():
        setattr(doctor, key, value)
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def delete_doctor(db: Session, doctor: Doctor) -> None:
    """Delete a doctor."""
    db.delete(doctor)
    db.commit()
