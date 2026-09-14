"""Department CRUD operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate


def get_by_id(db: Session, department_id: int) -> Department | None:
    """Fetch a department by id."""
    return db.get(Department, department_id)


def get_by_name(db: Session, name: str) -> Department | None:
    """Fetch a department by unique name."""
    stmt = select(Department).where(Department.name == name)
    return db.execute(stmt).scalar_one_or_none()


def list_departments(db: Session, skip: int = 0, limit: int = 50) -> list[Department]:
    """Return a page of departments."""
    stmt = select(Department).offset(skip).limit(limit).order_by(Department.id)
    return list(db.execute(stmt).scalars().all())


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    """Create a department."""
    department = Department(**payload.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def update_department(db: Session, department: Department, payload: DepartmentUpdate) -> Department:
    """Apply a partial department update."""
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(department, key, value)
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def delete_department(db: Session, department: Department) -> None:
    """Delete a department."""
    db.delete(department)
    db.commit()
